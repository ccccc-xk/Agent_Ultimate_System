"""
Mock API Server - zero dependency, no model download needed
Returns OpenAI-compatible JSON responses for 3 scenarios
"""
import json
import re
import time
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler

COMPLAINT_CATEGORIES = [
    (["wuliu", "kuaidi", "peisong", "fahuo", "songhuo", "yanchi"], "wuliu yanchi"),
    (["zhiliang", "huai le", "posun", "xiantou", "kaixian", "diaose"], "zhiliang wenti"),
    (["kefu", "taidu", "buhui", "buli", "fuwu"], "kefu taidu"),
]
COMPLAINT_CATEGORIES_CN = [
    (["物流", "快递", "配送", "发货", "送货", "延迟", "慢"], "物流延迟"),
    (["质量", "坏了", "破损", "线头", "开线", "掉色", "瑕疵"], "质量问题"),
    (["客服", "态度", "不回", "不理", "服务"], "客服态度"),
    (["价格", "贵", "降价", "差价"], "价格争议"),
    (["假货", "仿品", "山寨"], "商品真伪"),
]
COMPLAINT_DEMANDS = [
    (["退款", "退钱", "退货", "退换"], "退款"),
    (["赔偿", "赔钱", "补偿"], "赔偿"),
    (["道歉", "对不起"], "道歉"),
    (["换货", "换个", "更换"], "换货"),
    (["维修", "修理"], "维修"),
]

WORKORDER_MAP = {
    "空调": {"issue": "空调故障", "assigned_to": "维修部-李工"},
    "投影": {"issue": "投影仪故障", "assigned_to": "IT部-王工"},
    "wifi": {"issue": "网络故障", "assigned_to": "IT部-张工"},
    "WiFi": {"issue": "网络故障", "assigned_to": "IT部-张工"},
    "网络": {"issue": "网络故障", "assigned_to": "IT部-张工"},
    "打印机": {"issue": "打印机故障", "assigned_to": "IT部-赵工"},
    "电梯": {"issue": "电梯故障", "assigned_to": "物业-陈工"},
    "灯": {"issue": "照明故障", "assigned_to": "物业-刘工"},
    "水管": {"issue": "水管漏水", "assigned_to": "物业-陈工"},
    "门禁": {"issue": "门禁故障", "assigned_to": "物业-刘工"},
}

SQL_TEMPLATES = {
    "销售额": "SELECT p.product_name, SUM(o.amount) AS total_sales FROM orders o JOIN products p ON o.product_id = p.id WHERE o.order_date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH) GROUP BY p.product_name ORDER BY total_sales DESC LIMIT 10;",
    "员工": "SELECT e.name, d.department_name, e.salary FROM employees e JOIN departments d ON e.department_id = d.id ORDER BY e.salary DESC LIMIT 10;",
    "客户": "SELECT c.customer_name, COUNT(o.id) AS order_count, SUM(o.amount) AS total_amount FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.customer_name ORDER BY total_amount DESC LIMIT 10;",
    "订单": "SELECT id, customer_id, amount, order_date FROM orders WHERE order_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) ORDER BY order_date DESC;",
    "部门": "SELECT d.department_name, AVG(e.salary) AS avg_salary, COUNT(e.id) AS headcount FROM departments d JOIN employees e ON d.id = e.department_id GROUP BY d.department_name;",
    "产品": "SELECT product_name, price, stock FROM products WHERE stock > 0 ORDER BY price DESC;",
    "最高": "SELECT p.product_name, SUM(o.amount) AS total FROM orders o JOIN products p ON o.product_id = p.id GROUP BY p.product_name ORDER BY total DESC LIMIT 1;",
    "平均": "SELECT AVG(amount) AS avg_amount FROM orders WHERE order_date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH);",
}


def match_complaint(text):
    cats = []
    for keywords, label in COMPLAINT_CATEGORIES_CN:
        if any(k in text for k in keywords):
            cats.append(label)
    demands = []
    for keywords, label in COMPLAINT_DEMANDS:
        if any(k in text for k in keywords):
            demands.append(label)
    if not cats:
        cats = ["其他问题"]
    if not demands:
        demands = ["待确认"]
    cat_str = "、".join(cats)
    demand_str = "、".join(demands)
    return "\u3010\u5206\u7c7b\u3011\uff1a" + cat_str + "\n\u3010\u6838\u5fc3\u8bc9\u6c42\u3011\uff1a" + demand_str


def match_workorder(text):
    location = "\u672a\u8bc6\u522b"
    for pat in [r"(\d+\u697c)", r"(\d+\u5c42)", r"([\u4e00-\u9fff]+\u4f1a\u8bae\u5ba4)", r"([\u4e00-\u9fff]+\u529e\u516c\u5ba4)"]:
        m = re.search(pat, text)
        if m:
            location = m.group(1)
            break
    client = "\u672a\u8bc6\u522b"
    for pat in [r"([\u4e00-\u9fff]{2,4}(?:\u7ecf\u7406|\u603b|\u4e3b\u7ba1|\u4e3b\u4efb))"]:
        m = re.search(pat, text)
        if m:
            client = m.group(1)
            break
    issue = "\u5f85\u786e\u8ba4"
    assigned = "\u5f85\u5206\u914d"
    for kw, info in WORKORDER_MAP.items():
        if kw.lower() in text.lower():
            issue = info["issue"]
            assigned = info["assigned_to"]
            break
    priority = "\u4e2d"
    if any(w in text for w in ["\u7d27\u6025", "\u9a6c\u4e0a", "\u7acb\u523b", "\u5c3d\u5feb", "\u6025"]):
        priority = "\u9ad8"
    result = {
        "location": location,
        "client_name": client,
        "issue": issue,
        "actions_taken": ["\u5df2\u8bb0\u5f55\u5de5\u5355", "\u7b49\u5f85\u5904\u7406"],
        "assigned_to": assigned,
        "priority": priority,
    }
    return json.dumps(result, ensure_ascii=False)


def match_sql(text):
    for kw, sql in SQL_TEMPLATES.items():
        if kw in text:
            return sql
    return "SELECT id, name, created_at FROM orders ORDER BY created_at DESC LIMIT 10;"


def classify_and_respond(user_message):
    if any(w in user_message for w in ["\u6295\u8bc9", "\u5206\u7c7b"]):
        return match_complaint(user_message)
    if any(w in user_message for w in ["\u5de5\u5355", "json", "JSON", "\u62a5\u4fee"]):
        return match_workorder(user_message)
    if any(w in user_message for w in ["sql", "SQL", "查询", "SELECT"]):
        return match_sql(user_message)
    if any(w in user_message for w in ["\u9000", "\u8d54\u507f", "\u8d28\u91cf", "\u7269\u6d41", "\u5ba2\u670d"]):
        return match_complaint(user_message)
    if any(w in user_message for w in ["\u697c", "\u7a7a\u8c03", "wifi", "\u7f51\u7edc", "\u6253\u5370\u673a"]):
        return match_workorder(user_message)
    if any(w in user_message for w in ["\u9500\u552e\u989d", "\u5458\u5de5", "\u5ba2\u6237", "\u8ba2\u5355", "\u90e8\u95e8"]):
        return match_sql(user_message)
    return match_complaint(user_message)


class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/v1/models":
            resp = {"data": [{"id": "mock-vertical-model", "object": "model"}]}
        elif self.path == "/health":
            resp = {"status": "ok"}
        elif self.path == "/":
            resp = {"message": "Mock Vertical SFT API is running"}
        else:
            self.send_response(404)
            self.end_headers()
            return
        self._send_json(resp)

    def do_POST(self):
        if self.path == "/v1/chat/completions":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            messages = body.get("messages", [])
            user_msg = ""
            for m in messages:
                if m.get("role") == "user":
                    user_msg = m.get("content", "")
            reply = classify_and_respond(user_msg)
            resp = {
                "id": "chatcmpl-" + uuid.uuid4().hex[:12],
                "object": "chat.completion",
                "created": int(time.time()),
                "model": body.get("model", "mock-vertical-model"),
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": reply},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            }
        else:
            self.send_response(404)
            self.end_headers()
            return
        self._send_json(resp)

    def _send_json(self, data):
        out = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, fmt, *args):
        ts = time.strftime("%H:%M:%S")
        print(f"[{ts}] {args[0]}")


if __name__ == "__main__":
    PORT = 8001
    server = HTTPServer(("0.0.0.0", PORT), APIHandler)
    print(f"Mock API running at http://127.0.0.1:{PORT}")
    print("Endpoints: /v1/models, /v1/chat/completions, /health")
    print("Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")

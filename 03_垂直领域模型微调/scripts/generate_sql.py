#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
场景三：自然语言转 SQL — SFT 训练数据生成
instruction: "将自然语言问题转换为MySQL查询语句。"
output 为合法 SELECT 语句
"""

import json
import os
import random

SEED = 42
TARGET_COUNT = 60
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")

TIME_RANGES = {
    "上个月": "DATE_FORMAT(o.created_at, '%Y-%m') = DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 1 MONTH), '%Y-%m')",
    "本季度": "QUARTER(o.created_at) = QUARTER(CURDATE()) AND YEAR(o.created_at) = YEAR(CURDATE())",
    "今年": "YEAR(o.created_at) = YEAR(CURDATE())",
    "最近30天": "o.created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)",
}

# (自然语言, SQL) — 独立模板，不含占位符
STANDALONE_TEMPLATES = [
    ("查一下所有已付款的订单", "SELECT id, total_amount FROM orders WHERE status = '已付款';"),
    ("今年新入职的员工有多少", "SELECT COUNT(*) AS new_hires FROM employees WHERE hire_date >= DATE_FORMAT(CURDATE(), '%Y-01-01');"),
    ("查一下价格超过1000的产品", "SELECT name, price FROM products WHERE price > 1000 ORDER BY price DESC;"),
    ("上海地区的客户有多少", "SELECT COUNT(*) AS shanghai_customers FROM customers WHERE city = '上海';"),
    ("查一下上个月退货的订单", "SELECT id, total_amount, created_at FROM orders WHERE status = '已退货' AND DATE_FORMAT(created_at, '%Y-%m') = DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 1 MONTH), '%Y-%m');"),
    ("每个供应商的产品数量", "SELECT supplier, COUNT(*) AS product_count FROM products GROUP BY supplier ORDER BY product_count DESC;"),
    ("查一下年薪超过20万的员工", "SELECT name, salary, position FROM employees WHERE salary > 200000;"),
    ("每个城市的平均订单金额", "SELECT c.city, AVG(o.total_amount) AS avg_amount FROM orders o JOIN customers c ON o.customer_id = c.id GROUP BY c.city ORDER BY avg_amount DESC;"),
    ("查一下销量最好的产品类别", "SELECT p.category, SUM(o.quantity) AS total_sold FROM orders o JOIN products p ON o.product_id = p.id GROUP BY p.category ORDER BY total_sold DESC LIMIT 1;"),
    ("客户等级分布情况", "SELECT level, COUNT(*) AS cnt FROM customers GROUP BY level ORDER BY cnt DESC;"),
    ("查一下本月的订单总额", "SELECT SUM(total_amount) AS month_total FROM orders WHERE YEAR(created_at) = YEAR(CURDATE()) AND MONTH(created_at) = MONTH(CURDATE());"),
    ("工龄超过5年的员工名单", "SELECT name, hire_date, DATEDIFF(CURDATE(), hire_date) / 365 AS years FROM employees WHERE DATEDIFF(CURDATE(), hire_date) / 365 > 5;"),
    ("查一下各部门预算排名", "SELECT name, budget FROM departments ORDER BY budget DESC;"),
    ("库存最多的前3种产品", "SELECT name, stock FROM products ORDER BY stock DESC LIMIT 3;"),
    ("北京地区的VIP客户有哪些", "SELECT id, name, email FROM customers WHERE city = '北京' AND level = 'VIP';"),
    ("查一下每个部门有多少人", "SELECT d.name, COUNT(e.id) AS count FROM employees e JOIN departments d ON e.department_id = d.id GROUP BY d.id;"),
    ("订单金额超过5000的订单详情", "SELECT o.id, c.name, o.total_amount, o.created_at FROM orders o JOIN customers c ON o.customer_id = c.id WHERE o.total_amount > 5000;"),
    ("本月活跃客户数量", "SELECT COUNT(DISTINCT customer_id) AS active_customers FROM orders WHERE YEAR(created_at) = YEAR(CURDATE()) AND MONTH(created_at) = MONTH(CURDATE());"),
    ("查一下已发货但未付款的订单", "SELECT id, total_amount, created_at FROM orders WHERE status = '已发货';"),
    ("每种产品的利润率", "SELECT name, price, ROUND((price - price * 0.7) / price * 100, 2) AS margin_pct FROM products;"),
    ("查一下离职员工名单", "SELECT name, position, hire_date FROM employees WHERE status = '离职';"),
    ("VIP客户的总消费额", "SELECT SUM(o.total_amount) AS vip_total FROM orders o JOIN customers c ON o.customer_id = c.id WHERE c.level = 'VIP';"),
    ("查一下平均订单金额最高的城市", "SELECT c.city, AVG(o.total_amount) AS avg_order FROM orders o JOIN customers c ON o.customer_id = c.id GROUP BY c.city ORDER BY avg_order DESC LIMIT 1;"),
    ("研发部员工的平均薪资", "SELECT AVG(e.salary) AS avg_salary FROM employees e JOIN departments d ON e.department_id = d.id WHERE d.name = '研发部';"),
    ("查一下所有待处理的订单", "SELECT id, customer_id, total_amount FROM orders WHERE status = '待处理';"),
    ("每种商品的库存价值", "SELECT name, price, stock, ROUND(price * stock, 2) AS inventory_value FROM products ORDER BY inventory_value DESC;"),
    ("注册时间最近的10个客户", "SELECT id, name, registered_at FROM customers ORDER BY registered_at DESC LIMIT 10;"),
    ("订单数量超过5的客户", "SELECT c.id, c.name, COUNT(o.id) AS order_count FROM orders o JOIN customers c ON o.customer_id = c.id GROUP BY c.id, c.name HAVING COUNT(o.id) > 5 ORDER BY order_count DESC;"),
    ("查一下每个部门的最高薪资", "SELECT d.name, MAX(e.salary) AS max_salary FROM employees e JOIN departments d ON e.department_id = d.id GROUP BY d.id;"),
    ("销售部所有在职员工", "SELECT name, position, salary FROM employees e JOIN departments d ON e.department_id = d.id WHERE d.name = '销售部' AND e.status = '在职';"),
]


# 含占位符的模板
PARAM_TEMPLATES = [
    {
        "nl": "查一下{time_range}的订单总数",
        "sql": "SELECT COUNT(*) AS order_count FROM orders o WHERE {time_cond};",
    },
    {
        "nl": "{time_range}的总销售额是多少",
        "sql": "SELECT SUM(total_amount) AS total_sales FROM orders o WHERE {time_cond};",
    },
    {
        "nl": "查一下上个月销售额最高的产品是什么",
        "sql": "SELECT p.name, SUM(o.total_amount) AS total_sales FROM orders o JOIN products p ON o.product_id = p.id WHERE {time_cond} GROUP BY p.id, p.name ORDER BY total_sales DESC LIMIT 1;",
    },
    {
        "nl": "查一下{time_range}各部门的订单数",
        "sql": "SELECT d.name AS dept_name, COUNT(o.id) AS order_count FROM orders o JOIN employees e ON o.customer_id = e.id JOIN departments d ON e.department_id = d.id WHERE {time_cond} GROUP BY d.id, d.name;",
    },
    {
        "nl": "{time_range}新增了多少客户",
        "sql": "SELECT COUNT(*) AS new_customers FROM customers WHERE registered_at >= {time_cond};",
    },
    {
        "nl": "查一下{time_range}的平均订单金额",
        "sql": "SELECT AVG(total_amount) AS avg_amount FROM orders o WHERE {time_cond};",
    },
    {
        "nl": "{time_range}退货的订单有多少",
        "sql": "SELECT COUNT(*) AS return_count FROM orders o WHERE status = '已退货' AND {time_cond};",
    },
    {
        "nl": "查一下{time_range}销售额最高的部门",
        "sql": "SELECT d.name AS dept_name, SUM(o.total_amount) AS total_sales FROM orders o JOIN employees e ON o.customer_id = e.id JOIN departments d ON e.department_id = d.id WHERE {time_cond} GROUP BY d.id, d.name ORDER BY total_sales DESC LIMIT 1;",
    },
]


def fill_params(template, time_range_key):
    """填充含时间参数的模板"""
    nl = template["nl"].replace("{time_range}", time_range_key)
    sql = template["sql"].replace("{time_cond}", TIME_RANGES[time_range_key])
    return nl, sql


def main():
    random.seed(SEED)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    samples = []
    seen_sqls = set()
    time_range_keys = list(TIME_RANGES.keys())

    # Phase 1: 独立模板
    for nl, sql in STANDALONE_TEMPLATES:
        sql_key = sql.strip().lower()
        if sql_key not in seen_sqls:
            samples.append({"instruction": "将自然语言问题转换为MySQL查询语句。", "input": nl, "output": sql})
            seen_sqls.add(sql_key)

    # Phase 2: 参数模板 x 时间范围
    for tmpl in PARAM_TEMPLATES:
        for tr_key in time_range_keys:
            nl, sql = fill_params(tmpl, tr_key)
            sql_key = sql.strip().lower()
            if sql_key not in seen_sqls:
                samples.append({"instruction": "将自然语言问题转换为MySQL查询语句。", "input": nl, "output": sql})
                seen_sqls.add(sql_key)

    # Phase 3: 截取或扩展
    if len(samples) > TARGET_COUNT:
        samples = samples[:TARGET_COUNT]
    elif len(samples) < TARGET_COUNT:
        # 用已有独立模板生成自然语言变体
        prefixes = ["帮我查一下", "我想看看", "请统计", "现在", "", "", "", ""]
        extras = [
            ("查一下所有已付款的订单", "SELECT id, total_amount FROM orders WHERE status = '已付款';"),
            ("今年新入职的员工", "SELECT COUNT(*) FROM employees WHERE hire_date >= DATE_FORMAT(CURDATE(), '%Y-01-01');"),
        ]
        attempt = 0
        while len(samples) < TARGET_COUNT and attempt < 200:
            attempt += 1
            if random.random() < 0.5 and extras:
                # 用已有SQL但换自然语言表述
                tmpl = random.choice(extras)
                prefix = random.choice(prefixes)
                nl = prefix + tmpl[0]
                sql_key = tmpl[1].strip().lower()
            else:
                tmpl = random.choice(PARAM_TEMPLATES)
                tr_key = random.choice(time_range_keys)
                nl, sql = fill_params(tmpl, tr_key)
                sql_key = sql.strip().lower()
            if sql_key not in seen_sqls:
                samples.append({"instruction": "将自然语言问题转换为MySQL查询语句。", "input": nl, "output": sql})
                seen_sqls.add(sql_key)

    output_path = os.path.join(OUTPUT_DIR, "nl2sql.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)

    print(f"[自然语言转SQL] 生成完成: {len(samples)} 条")
    print(f"  输出路径: {output_path}")

    return samples


if __name__ == "__main__":
    main()

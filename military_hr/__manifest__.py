{
    "name": "Military HR",
    "summary": """
        Military HR
        """,
    "author": "Yevhen Babii",
    "website": "https://github.com/yevhenbabii/odoo-military-addons",
    "category": "Human Resources",
    "version": "1.0.0",
    "license": "Other proprietary",
    "depends": [
        "base",
        "contacts",
        "military_company",
        "declension_ua",
    ],
    "demo": [
        "demo/military.department.csv",
        "demo/military.job.csv",
        "demo/military.employee.csv",
    ],
    "data": [
        "security/military_hr_security.xml",
        "security/ir.model.access.csv",
        "views/military_employee.xml",
        "views/military_employee_location.xml",
        "views/military_department.xml",
        "views/military_rank.xml",
        "views/military_job.xml",
        "views/military_rank_assign.xml",
        "views/military_job_assign.xml",
        # "report/form5.xml",
        "views/menu.xml",
    ],
    "sequence": '0',
}

    1 root/
    2 ├── api/
    3 │   ├── v1/
    4 │   │   ├── auth/
    5 │   │   │   ├── google_auth.py
    6 │   │   │   ├── login.py
    7 │   │   │   └── register.py
    8 │   │   ├── payments.py
    9 │   │   ├── reviews.py
   10 │   │   └── users.py
   11 │   └── dependencies.py
   12 ├── crud/
   13 │   ├── payment.py
   14 │   ├── plan.py
   15 │   ├── review.py
   16 │   └── user.py
   17 ├── database/
   18 │   ├── __init__.py
   19 │   ├── base.py
   20 │   └── session.py
   21 ├── models/
   22 │   ├── __init__.py
   23 │   ├── payment.py
   24 │   ├── plan.py
   25 │   ├── review.py
   26 │   └── user.py
   27 ├── schemas/
   28 │   ├── auth.py
   29 │   ├── payment.py
   30 │   ├── plan.py
   31 │   ├── review.py
   32 │   └── user.py
   33 ├── .gitignore
   34 ├── .python-version
   35 ├── config.py
   36 ├── main.py
   37 ├── pyproject.toml
   38 ├── README.md
   39 ├── security.py
   40 ├── summary.md
   41 ├── test.py
   42 └── uv.lock
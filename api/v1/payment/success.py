from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Payment"])


@router.get("/success", response_class=HTMLResponse)
async def payment_success():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Payment Successful | نجاح الدفع</title>

        <style>
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }

            body {
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                background: #f7f7f7;
                font-family: Arial, sans-serif;
                color: #222;
            }

            .card {
                width: min(90%, 480px);
                padding: 48px 40px;
                background: white;
                border-radius: 16px;
                text-align: center;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
            }

            .icon {
                width: 70px;
                height: 70px;
                margin: 0 auto 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                background: green;
                color: white;
                font-size: 36px;
            }

            h1 {
                margin-bottom: 12px;
                font-size: 28px;
            }

            .message {
                margin-bottom: 28px;
                color: #666;
                line-height: 1.6;
                color:gray;
                font-wight : 600
            }

            .arabic {
                direction: rtl;
                font-family: Arial, sans-serif;
            }

            .button {
                display: inline-block;
                padding: 12px 24px;
                border-radius: 8px;
                background: #111;
                color: white;
                text-decoration: none;
                font-weight: 600;
            }

            .button:hover {
                opacity: 0.9;
            }
        </style>
    </head>

    <body>
        <main class="card">

            <div class="icon"><svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 16 16">
                <path d="M0 0h16v16H0z" fill="none" />
                <path fill="currentColor" d="M12.736 3.97a.733.733 0 0 1 1.047 0c.286.289.29.756.01 1.05L7.88 12.01a.733.733 0 0 1-1.065.02L3.217 8.384a.757.757 0 0 1 0-1.06a.733.733 0 0 1 1.047 0l3.052 3.093l5.4-6.425z" />
                </svg>
            </div>

            <h1>Payment Successful</h1>
            <h1 class="arabic">تم الدفع بنجاح</h1>

            <p class="message">
                Your payment has been completed successfully.
                One of our team members will contact you shortly.
            </p>

            <p class="message arabic">
                تم إتمام عملية الدفع بنجاح.
                سيتواصل معك أحد أعضاء فريقنا قريبًا.
            </p>

            <a class="button" href="https://badiaprojectmanagement.com">
                Return to Home Page
            </a>

        </main>
    </body>
    </html>
    """
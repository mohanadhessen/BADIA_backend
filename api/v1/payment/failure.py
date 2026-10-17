from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Payment"])


@router.get("/failure", response_class=HTMLResponse)
async def payment_failure():
    return """
    <!DOCTYPE html>
    <html lang="en">

    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Payment Failed | فشل الدفع</title>

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
                background: #d32f2f;
                color: white;
                font-size: 36px;
            }

            .icon svg {
                width: 36px;
                height: 36px;
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

            <div class="icon">
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="1em"
                    height="1em"
                    viewBox="0 0 16 16"
                >
                    <path d="M0 0h16v16H0z" fill="none" />
                    <path
                        fill="currentColor"
                        d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8L4.646 5.354a.5.5 0 0 1 0-.708"
                    />
                </svg>
            </div>

            <h1>Payment Failed</h1>
            <h1 class="arabic">فشل الدفع</h1>

            <p class="message">
                Your payment could not be completed.
                Please try again or contact our team if the problem persists.
            </p>

            <p class="message arabic">
                تعذر إتمام عملية الدفع.
                يرجى المحاولة مرة أخرى أو التواصل مع فريقنا إذا استمرت المشكلة.
            </p>

            <a class="button" href="https://badiaprojectmanagement.com">
                Return to Home Page
            </a>

        </main>
    </body>

    </html>
    """
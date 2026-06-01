const API_URL =
    "http://127.0.0.1:8000/chat";

async function sendMessage() {

    const input =
        document.getElementById(
            "question"
        );

    const question =
        input.value.trim();

    if (!question) return;

    const chat =
        document.getElementById(
            "chat-box"
        );

    const welcome =
        document.getElementById(
            "welcome"
        );

    if (welcome) {
        welcome.style.display =
            "none";
    }

    chat.innerHTML += `
        <div class="user">
            ${question}
        </div>
    `;

    input.value = "";

    chat.scrollTop =
        chat.scrollHeight;

    const typingId =
        "typing-" +
        Date.now();

    chat.innerHTML += `
        <div
            class="bot"
            id="${typingId}"
        >
            Thinking...
        </div>
    `;

    chat.scrollTop =
        chat.scrollHeight;

    try {

        const response =
            await fetch(
                API_URL,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                        "application/json"
                    },

                    body:
                    JSON.stringify({
                        question
                    })
                }
            );

        const data =
            await response.json();

        const typing =
            document.getElementById(
                typingId
            );

        if (typing) {
            typing.remove();
        }

        chat.innerHTML += `
            <div class="bot">
                ${data.answer}
            </div>
        `;

        chat.scrollTop =
            chat.scrollHeight;

    } catch (error) {

        const typing =
            document.getElementById(
                typingId
            );

        if (typing) {
            typing.remove();
        }

        chat.innerHTML += `
            <div class="bot">
                ❌ Unable to connect
                to backend.
            </div>
        `;

        console.error(error);
    }
}

/* Suggestion buttons */

function askSuggestion(
    question
) {

    document.getElementById(
        "question"
    ).value = question;

    sendMessage();
}

/* Enter key support */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        const input =
            document.getElementById(
                "question"
            );

        input.addEventListener(
            "keypress",
            function(event) {

                if (
                    event.key ===
                    "Enter"
                ) {

                    sendMessage();
                }
            }
        );
    }
);
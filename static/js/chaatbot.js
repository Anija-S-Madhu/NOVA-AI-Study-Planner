document.addEventListener("DOMContentLoaded", () => {

    const box = document.getElementById("box");
    const input = document.getElementById("message");
    const send = document.getElementById("send");
    const clear = document.getElementById("clear");
    const doc = document.getElementById("doc");

    if (!box || !input || !send || !clear) return;

    let sending = false;

    function addMessage(role, content) {
        const message = document.createElement("div");
        message.className = `message ${role}`;

        const text = document.createElement("div");
        text.textContent = content;

        message.appendChild(text);
        box.appendChild(message);

        box.scrollTop = box.scrollHeight;

        return message;
    }

    async function sendMessage() {

        const message = input.value.trim();

        if (!message || sending) return;

        addMessage("user", message);

        input.value = "";
        sending = true;
        send.disabled = true;

        const loading = addMessage(
            "assistant",
            "NOVA is thinking..."
        );

        try {

            const response = await fetch("/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify({
                    message: message,
                    document_id: doc ? doc.value || null : null
                })
            });

            const data = await response.json();

            loading.remove();

            if (!response.ok) {
                addMessage("assistant", data.error || "Something went wrong.");
            } else {
                addMessage("assistant", data.reply || "No response received.");
            }

        } catch (error) {

            loading.remove();

            addMessage(
                "assistant",
                "Connection error. Please try again."
            );

            console.error(error);

        } finally {

            sending = false;
            send.disabled = false;
            input.focus();

        }
    }

    send.addEventListener("click", sendMessage);

    input.addEventListener("keydown", event => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });

    clear.addEventListener("click", async () => {

        if (sending) return;

        if (!confirm("Clear your chat history?")) return;

        try {

            const response = await fetch("/chat/clear", {
                method: "POST",
                headers: {
                    "Accept": "application/json"
                }
            });

            const data = await response.json();

            if (!response.ok || !data.ok) {
                throw new Error(data.error || "Unable to clear chat.");
            }

            box.replaceChildren();

            addMessage(
                "assistant",
                "Hi! I'm NOVA, your AI study tutor. How can I help you today?"
            );

        } catch (error) {

            alert(error.message);

        }

    });

    box.scrollTop = box.scrollHeight;

});

const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("user-message");
const chatMessages = document.getElementById("chat-messages");

function addMessage(message, sender) {
    const messageDiv = document.createElement("div");

    messageDiv.classList.add(
        sender === "user" ? "user-message" : "bot-message"
    );

    messageDiv.textContent = message;

    chatMessages.appendChild(messageDiv);

    messageDiv.scrollIntoView({ behavior: "smooth" });
}

chatForm.addEventListener("submit", async function(event) {
    event.preventDefault();

    const userMessage = messageInput.value.trim();

    if (!userMessage) return;

    addMessage(userMessage, "user");

    messageInput.value = "";
    messageInput.disabled = true;

    const loadingMessage = document.createElement("div");
    loadingMessage.classList.add("bot-message");
    loadingMessage.textContent = "QuickCart is thinking...";

    chatMessages.appendChild(loadingMessage);

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: userMessage
            })
        });

        if (!response.ok) {
            throw new Error("Server error: " + response.status);
        }

        const data = await response.json();

        loadingMessage.remove();

        addMessage(data.response, "bot");

    } catch (error) {
        loadingMessage.remove();

        addMessage(
            "Sorry! Something went wrong. Please try again.",
            "bot"
        );

        console.error(error);

    } finally {
        messageInput.disabled = false;
        messageInput.focus();
    }
});

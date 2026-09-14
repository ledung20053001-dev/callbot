"use strict";

const { normalizeTranscriptText } = window.CallbotText;

const session = { callId: null, busy: false };

const elements = {
  startForm: document.querySelector("#start-form"),
  startButton: document.querySelector("#start-button"),
  direction: document.querySelector("#direction"),
  callerNumber: document.querySelector("#caller-number"),
  messageForm: document.querySelector("#message-form"),
  messageInput: document.querySelector("#message-input"),
  sendButton: document.querySelector("#send-button"),
  voiceButton: document.querySelector("#voice-button"),
  voiceStatus: document.querySelector("#voice-status"),
  voiceHelp: document.querySelector("#voice-help"),
  transcript: document.querySelector("#transcript"),
  transcriptEmpty: document.querySelector("#transcript-empty"),
  eventList: document.querySelector("#event-list"),
  clearEvents: document.querySelector("#clear-events"),
  stateValue: document.querySelector("#state-value"),
  verifiedValue: document.querySelector("#verified-value"),
  callIdValue: document.querySelector("#call-id-value"),
  recordValue: document.querySelector("#record-value"),
  connectionLabel: document.querySelector("#connection-label"),
  toast: document.querySelector("#toast"),
};

function setBusy(isBusy, label = "Đang xử lý") {
  session.busy = isBusy;
  elements.connectionLabel.dataset.busy = String(isBusy);
  delete elements.connectionLabel.dataset.error;
  elements.connectionLabel.textContent = isBusy ? label.toUpperCase() : "READY";
  elements.startButton.disabled = isBusy;
  elements.sendButton.disabled = isBusy || !session.callId;
  elements.messageInput.disabled = isBusy || !session.callId;
  elements.voiceButton.disabled = isBusy || !session.callId || !speechRecognition;
}

function showError(message) {
  elements.connectionLabel.dataset.error = "true";
  elements.connectionLabel.textContent = "ERROR";
  elements.toast.textContent = message;
  elements.toast.hidden = false;
  window.setTimeout(() => { elements.toast.hidden = true; }, 5000);
}

function updateState(data) {
  elements.stateValue.textContent = data.state;
  elements.stateValue.dataset.tone = data.state === "ENDED" ? "success" : "pending";
  elements.verifiedValue.textContent = String(data.verified_identity).toUpperCase();
  elements.verifiedValue.dataset.tone = data.verified_identity ? "success" : "pending";
  elements.callIdValue.textContent = data.call_id ?? session.callId ?? "—";
  const guardLabel = elements.recordValue.querySelector("span");
  const guardMessage = elements.recordValue.querySelector("p");
  guardLabel.textContent = data.verified_identity
    ? "CORE GUARD · VERIFIED"
    : "CORE GUARD · LOCKED";
  guardMessage.textContent = data.verified_identity
    ? "Danh tính đã xác minh. UI vẫn chỉ hiển thị dữ liệu được Bot API trả về."
    : "Chi tiết lịch hẹn chỉ hiển thị sau khi danh tính được xác minh qua Bot API.";
}

function appendTranscript(role, text) {
  const normalizedText = normalizeTranscriptText(text);
  if (!normalizedText) return;
  elements.transcriptEmpty?.remove();
  const row = document.createElement("article");
  row.className = "transcript-line";
  row.dataset.role = role;

  const label = document.createElement("span");
  label.className = "transcript-role";
  label.textContent = role === "user" ? "Caller" : "Bot";

  const content = document.createElement("p");
  content.className = "transcript-text";
  content.textContent = normalizedText;

  row.append(label, content);
  elements.transcript.append(row);
  row.scrollIntoView({ block: "end", behavior: "smooth" });
}

function logApi(method, path, status, failed = false) {
  elements.eventList.querySelector(".empty-event")?.remove();
  const item = document.createElement("li");
  const time = new Date().toLocaleTimeString("vi-VN", { hour12: false });

  for (const [className, value] of [
    ["event-time", time],
    ["event-method", method],
    ["event-path", path],
    ["event-status", String(status)],
  ]) {
    const span = document.createElement("span");
    span.className = className;
    span.textContent = value;
    if (className === "event-status") span.dataset.error = String(failed);
    item.append(span);
  }
  elements.eventList.prepend(item);
}

async function callBotApi(path, options) {
  const method = options.method ?? "GET";
  setBusy(true, method === "POST" ? "Đang gọi Bot API" : "Đang tải");
  try {
    const response = await fetch(path, {
      ...options,
      headers: { "Content-Type": "application/json", ...options.headers },
    });
    logApi(method, path, response.status, !response.ok);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail ?? "Bot API trả về lỗi.");
    return data;
  } catch (error) {
    if (error instanceof TypeError) logApi(method, path, "OFFLINE", true);
    throw error;
  } finally {
    setBusy(false);
  }
}

elements.startForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const data = await callBotApi("/v1/calls", {
      method: "POST",
      body: JSON.stringify({
        direction: elements.direction.value,
        caller_number: elements.callerNumber.value.trim() || null,
      }),
    });
    session.callId = data.call_id;
    elements.transcript.replaceChildren();
    updateState(data);
    appendTranscript("bot", data.reply);
    setBusy(false);
    elements.messageInput.focus();
  } catch (error) {
    showError(error instanceof Error ? error.message : "Không thể bắt đầu cuộc gọi.");
  }
});

elements.messageForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = normalizeTranscriptText(elements.messageInput.value);
  if (!text || !session.callId || session.busy) return;

  appendTranscript("user", text);
  elements.messageInput.value = "";
  try {
    const path = `/v1/calls/${encodeURIComponent(session.callId)}/turn`;
    const data = await callBotApi(path, {
      method: "POST",
      body: JSON.stringify({ text }),
    });
    updateState(data);
    appendTranscript("bot", data.reply);
  } catch (error) {
    showError(error instanceof Error ? error.message : "Không thể gửi lượt hội thoại.");
  }
});

elements.messageInput.addEventListener("keydown", (event) => {
  if (event.ctrlKey && event.key === "Enter") {
    event.preventDefault();
    elements.messageForm.requestSubmit();
  }
});

elements.clearEvents.addEventListener("click", () => {
  elements.eventList.replaceChildren();
  const empty = document.createElement("li");
  empty.className = "empty-event";
  empty.textContent = "Chưa có request nào.";
  elements.eventList.append(empty);
});

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const speechRecognition = SpeechRecognition ? new SpeechRecognition() : null;

if (speechRecognition) {
  speechRecognition.lang = "vi-VN";
  speechRecognition.interimResults = false;
  speechRecognition.continuous = false;
  elements.voiceHelp.textContent = "Giọng nói được chuyển thành văn bản trước khi gửi Bot API.";

  speechRecognition.addEventListener("start", () => {
    elements.voiceStatus.textContent = "VOICE · LISTENING";
    elements.voiceStatus.dataset.active = "true";
    elements.voiceButton.dataset.active = "true";
    elements.voiceButton.setAttribute("aria-label", "Đang nhận giọng nói");
  });
  speechRecognition.addEventListener("result", (event) => {
    const text = normalizeTranscriptText(event.results[0][0].transcript);
    elements.messageInput.value = text;
    elements.voiceStatus.textContent = "VOICE · TRANSCRIBED";
    elements.messageForm.requestSubmit();
  });
  speechRecognition.addEventListener("error", (event) => {
    showError(`Không thể nhận giọng nói: ${event.error}`);
  });
  speechRecognition.addEventListener("end", () => {
    elements.voiceStatus.textContent = "VOICE · INACTIVE";
    delete elements.voiceStatus.dataset.active;
    delete elements.voiceButton.dataset.active;
    elements.voiceButton.setAttribute("aria-label", "Bắt đầu nhận giọng nói");
  });
  elements.voiceButton.addEventListener("click", () => speechRecognition.start());
} else {
  elements.voiceHelp.textContent = "Trình duyệt này không hỗ trợ Speech Recognition.";
}

elements.startButton.disabled = false;
elements.connectionLabel.textContent = "READY · V6";
elements.connectionLabel.dataset.uiReady = "true";

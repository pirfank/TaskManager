let notificationsEnabled = false;

console.log("notify.js loaded");

function enableNotifications() {
  if (!("Notification" in window)) {
    alert("Notifications not supported");
    return;
  }

  Notification.requestPermission().then(permission => {
    if (permission === "granted") {
      notificationsEnabled = true;

      speak("Task reminders enabled");
      new Notification("⏰ Task reminders enabled");

      scheduleReminders();
    } else {
      alert("Permission denied");
    }
  });
}

function speak(text) {
  if (!("speechSynthesis" in window)) return;

  const msg = new SpeechSynthesisUtterance(text);
  msg.lang = "en-US";
  msg.rate = 1;
  msg.pitch = 1;
  speechSynthesis.speak(msg);
}

function scheduleReminders() {
  if (!notificationsEnabled) return;

  const app = document.getElementById("app");
  const nickname = app.dataset.nickname || "Hey";

  const tasks = document.querySelectorAll(".task");

  tasks.forEach(task => {
    // Skip completed tasks
    if (task.classList.contains("done")) return;

    const taskText = task.dataset.task;
    const dueTime = new Date(task.dataset.due).getTime();
    const now = Date.now();

    if (dueTime <= now) return;

    const delay = dueTime - now;

    console.log(
      `Reminder scheduled for "${taskText}" in ${Math.round(delay / 1000)}s`
    );

    setTimeout(() => {
      const message =
        `${nickname}, your ${taskText} time has arrived`;

      new Notification("⏰ Task Reminder", {
        body: message
      });

      speak(message);

    }, delay);
  });
}

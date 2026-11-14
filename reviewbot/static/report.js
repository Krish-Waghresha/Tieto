(function () {
  "use strict";
  var data = JSON.parse(document.getElementById("data").textContent);
  var $ = function (id) { return document.getElementById(id); };
  var quizScore = null;

  // reveal recommendation only after the reviewer chose (anti-anchoring)
  document.querySelectorAll("fieldset.verdict").forEach(function (fs) {
    var card = fs.closest(".card"), rec = card && card.querySelector("details.rec");
    if (rec) { rec.hidden = true; }
    fs.addEventListener("change", function () { if (rec) { rec.hidden = false; } });
  });

  $("quizcheck").addEventListener("click", function () {
    var right = 0, total = 0;
    document.querySelectorAll("fieldset.q").forEach(function (fs) {
      var ans = fs.getAttribute("data-answer"), sel = fs.querySelector("input:checked");
      var ex = fs.querySelector(".explain");
      if (ans === "") { return; }
      total += 1;
      var ok = sel && sel.value === ans;
      if (ok) { right += 1; }
      fs.classList.toggle("right", !!ok); fs.classList.toggle("wrong", !ok);
      if (ex) { ex.hidden = false; }
    });
    quizScore = right + "/" + total;
    $("quizscore").textContent = "Score " + quizScore + " — recorded in your /sign comment, does not block merge.";
  });

  $("play").addEventListener("click", function () {
    if (!("speechSynthesis" in window)) { $("audiotext").closest("details").open = true; return; }
    window.speechSynthesis.cancel();
    var u = new SpeechSynthesisUtterance(data.audio); u.rate = 1.02; window.speechSynthesis.speak(u);
  });
  $("stop").addEventListener("click", function () { if ("speechSynthesis" in window) { window.speechSynthesis.cancel(); } });

  function clean(s) { return String(s || "").replace(/[\r\n]+/g, " ").slice(0, 400); }

  $("gensign").addEventListener("click", function () {
    var lines = ["/sign", "head: " + data.head, "ledger: " + data.ledger, "decision: " + $("decision").value];
    var missing = [];
    data.items.forEach(function (id) {
      var sel = document.querySelector('input[name="v-' + id + '"]:checked');
      if (sel) { lines.push(id + ": " + sel.value); } else { missing.push(id); lines.push(id + ": UNRESOLVED"); }
    });
    var free = document.querySelector('textarea[name="Q4"]');
    lines.push("quiz: " + (quizScore || "not taken"));
    if (free && free.value) { lines.push("could_break: " + clean(free.value)); }
    lines.push("residual_risk: " + (clean($("risk").value) || "none stated"));
    $("signout").textContent = lines.join("\n") + (missing.length ? "\n\n⚠ unresolved: " + missing.join(", ") + " — the bot will reject this record." : "");
  });
  $("copysign").addEventListener("click", function () {
    var t = $("signout").textContent.split("\n\n⚠")[0];
    if (navigator.clipboard) { navigator.clipboard.writeText(t); }
  });
}());

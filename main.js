const API_URL = "https://peps.python.org/api/python-releases.json";

function daysUntil(dateStr) {
  const [y, m, d] = dateStr.split("-").map(Number);
  const release = new Date(y, m - 1, d);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((release - today) / 86400000);
}

function getTodayStr() {
  const now = new Date();
  const y = now.getFullYear();
  const m = now.getMonth() + 1;
  const d = now.getDate();
  return `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
}

function formatDate(dateStr) {
  const [year, month, day] = dateStr.split("-").map(Number);
  return new Date(year, month - 1, day).toLocaleDateString("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

function getDaysClass(days) {
  if (days === 0) return "today";
  if (days <= 7) return "soon";
  if (days <= 30) return "near";
  return "";
}

function createReleaseItem(release) {
  const pep = release.pep;
  let pepHtml = "";
  if (pep) {
    const pepStr = String(pep).padStart(4, "0");
    const pepUrl = `https://peps.python.org/pep-${pepStr}/`;
    pepHtml = ` · <a href="${pepUrl}" class="pep-link">PEP ${pep}</a>`;
  }
  let noteHtml = "";
  if (release.note) {
    noteHtml = `<span class="note"> — ${release.note}</span>`;
  }
  return `<div class="release-item"><span class="release-name">${release.stage}</span>${pepHtml}${noteHtml}</div>`;
}

function createDateGroup(dateStr, releases, isNext = false) {
  const days = daysUntil(dateStr);
  const daysClass = getDaysClass(days);
  let daysText;
  if (days === 0) {
    daysText = "Today!";
  } else if (days === 1) {
    daysText = "1 day";
  } else {
    daysText = `${days} days`;
  }
  const cardClass = isNext ? "release-card next" : "release-card";
  const itemsHtml = releases.map(createReleaseItem).join("");
  return `<div class="${cardClass}">
    <div class="release-header">
        <span class="release-date">${formatDate(dateStr)}</span>
        <span class="days-until ${daysClass}">${daysText}</span>
    </div>
    ${itemsHtml}
</div>`;
}

function render(data) {
  const content = document.getElementById("content");
  try {
    const releasesData = data.releases || {};
    const metadata = data.metadata || {};
    const todayStr = getTodayStr();
    const upcoming = [];

    for (const [version, releases] of Object.entries(releasesData)) {
      const pep = metadata[version]?.pep;
      for (const release of releases) {
        if (release.state === "expected" && release.date >= todayStr) {
          upcoming.push({
            stage: release.stage,
            date: release.date,
            note: release.note || "",
            pep,
          });
        }
      }
    }

    upcoming.sort((a, b) => {
      if (a.date !== b.date) return a.date.localeCompare(b.date);
      return a.stage.localeCompare(b.stage);
    });

    if (upcoming.length === 0) {
      content.innerHTML =
        '<div class="no-releases">No upcoming releases scheduled.</div>';
      return;
    }

    const grouped = Object.groupBy(upcoming, (r) => r.date);
    const sortedDates = Object.keys(grouped).sort();
    const nextDate = sortedDates[0];

    let html = "";
    for (const date of sortedDates) {
      const isNext = date === nextDate;
      html += createDateGroup(date, grouped[date], isNext);
    }
    content.innerHTML = html;
  } catch (e) {
    content.innerHTML = `<div class="no-releases">Error: ${e}</div>`;
  }
}

fetch(API_URL)
  .then((response) => response.json())
  .then(render)
  .catch((e) => {
    document.getElementById("content").innerHTML =
      `<div class="no-releases">Error: ${e}</div>`;
  });

from pyscript import document
from js import fetch, JSON, Date

API_URL = "https://peps.python.org/api/python-releases.json"


def date_to_days(year, month, day):
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    days = day
    for m in range(1, month):
        days += days_in_month[m - 1]
        if m == 2 and (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)):
            days += 1
    days += year * 365 + year // 4 - year // 100 + year // 400
    return days


def days_until(release_date):
    ry = int(release_date[:4])
    rm = int(release_date[5:7])
    rd = int(release_date[8:10])
    now = Date.new()
    ty, tm, td = now.getFullYear(), now.getMonth() + 1, now.getDate()
    return date_to_days(ry, rm, rd) - date_to_days(ty, tm, td)


def get_today_str():
    now = Date.new()
    y = now.getFullYear()
    m = now.getMonth() + 1
    d = now.getDate()
    return f"{y}-{('0' + str(m))[-2:]}-{('0' + str(d))[-2:]}"


MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def get_weekday(year, month, day):
    if month < 3:
        month += 12
        year -= 1
    k = year % 100
    j = year // 100
    h = (day + (13 * (month + 1)) // 5 + k + k // 4 + j // 4 - 2 * j) % 7
    return (h + 5) % 7


def format_date(date_str):
    year = int(date_str[:4])
    month = int(date_str[5:7])
    day = int(date_str[8:10])
    weekday = DAY_NAMES[get_weekday(year, month, day)]
    return f"{weekday}, {day} {MONTH_NAMES[month]} {year}"


def get_days_class(days):
    if days == 0:
        return "today"
    if days <= 7:
        return "soon"
    if days <= 30:
        return "near"
    return ""


def create_release_item(release):
    pep = release.get("pep")
    pep_html = ""
    if pep:
        pep_str = ("000" + str(pep))[-4:]
        pep_url = f"https://peps.python.org/pep-{pep_str}/"
        pep_html = f' · <a href="{pep_url}" class="pep-link">PEP {pep}</a>'
    note_html = ""
    if release.get("note"):
        note_html = f'<span class="note"> — {release["note"]}</span>'
    return f'<div class="release-item"><span class="release-name">{release["stage"]}</span>{pep_html}{note_html}</div>'


def create_date_group(date_str, releases, is_next=False):
    days = days_until(date_str)
    days_class = get_days_class(days)
    if days == 0:
        days_text = "Today!"
    elif days == 1:
        days_text = "1 day"
    else:
        days_text = f"{days} days"
    card_class = "release-card next" if is_next else "release-card"
    items_html = "".join(create_release_item(r) for r in releases)
    return f'''<div class="{card_class}">
    <div class="release-header">
        <span class="release-date">{format_date(date_str)}</span>
        <span class="days-until {days_class}">{days_text}</span>
    </div>
    {items_html}
</div>'''


def render(data):
    content = document.getElementById("content")
    try:
        releases_data = data.get("releases", {})
        metadata = data.get("metadata", {})
        today_str = get_today_str()
        upcoming = []
        for version, releases in releases_data.items():
            pep = metadata.get(version, {}).get("pep")
            for release in releases:
                if release.get("state") == "expected":
                    if release["date"] >= today_str:
                        upcoming.append({
                            "version": version,
                            "stage": release["stage"],
                            "state": release["state"],
                            "date": release["date"],
                            "note": release.get("note", ""),
                            "pep": pep
                        })
        upcoming.sort(key=lambda x: (x["date"], x["stage"]))
        if not upcoming:
            content.innerHTML = '<div class="no-releases">No upcoming releases scheduled.</div>'
            return
        # Group by date
        grouped = {}
        for release in upcoming:
            date = release["date"]
            if date not in grouped:
                grouped[date] = []
            grouped[date].append(release)
        sorted_dates = sorted(grouped.keys())
        next_date = sorted_dates[0]
        html = ""
        for date in sorted_dates:
            is_next = date == next_date
            html += create_date_group(date, grouped[date], is_next)
        content.innerHTML = html
    except Exception as e:
        content.innerHTML = f'<div class="no-releases">Error: {e}</div>'


def on_response(response):
    response.json().then(on_json)


def on_json(json_data):
    data_str = JSON.stringify(json_data)
    import json
    data = json.loads(data_str)
    render(data)


def on_error(e):
    document.getElementById("content").innerHTML = f'<div class="no-releases">Error: {e}</div>'


fetch(API_URL).then(on_response).catch(on_error)

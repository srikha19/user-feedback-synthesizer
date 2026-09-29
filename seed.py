import json
import time
import urllib.request

URL = "http://127.0.0.1:5000/analyze"

# (date, channel, customer, text)
DATA = [
    ("2026-08-25", "App Review", "Rahul Sharma", "Product search is painfully slow. It takes about 8 seconds to show results and I often give up."),
    ("2026-08-27", "Support Ticket", "Priya Nair", "Search keeps timing out when I filter by category. This is blocking my team's daily work."),
    ("2026-08-29", "Sales Call", "Arjun Mehta (Acme Corp)", "We love the dashboards, but search performance is the main reason we are hesitating to renew our contract."),
    ("2026-09-01", "Email", "Sneha Reddy", "Search is too slow on mobile. Please fix it, my customers are complaining to me."),
    ("2026-09-03", "App Review", "Vikram Singh", "Great design, but the search lag makes the app feel unusable. Two stars for now."),
    ("2026-09-05", "Survey", "Ananya Iyer", "The onboarding was smooth and the support team was helpful. Search speed could be better."),
    ("2026-09-08", "Support Ticket", "Karan Patel", "Search results take forever to load for large catalogs. Third time I am reporting this."),
    ("2026-09-10", "Sales Call", "Meera Joshi (Zenith Retail)", "Our biggest blocker is slow search. If it is not fixed this quarter we will evaluate competitors."),
    ("2026-09-18", "Product Update", "", "Shipped search performance update: new indexing cut average search time from 8 seconds to under 1 second."),
    ("2026-09-20", "App Review", "Rohit Verma", "Search is finally fast! Huge improvement, thank you. Really happy with the update."),
    ("2026-09-21", "Email", "Sneha Reddy", "Thanks for fixing search, it works great now. My customers stopped complaining about it."),
    ("2026-09-22", "Support Ticket", "Divya Menon", "Checkout keeps failing with a payment error when I use UPI. I tried three times and lost my cart."),
    ("2026-09-23", "App Review", "Amit Kulkarni", "Payment fails at checkout every time. Search is fast now but I cannot buy anything. One star."),
    ("2026-09-25", "Sales Call", "Arjun Mehta (Acme Corp)", "Search is much better and we are planning to renew, but our team hit payment failures during checkout and needs that fixed."),
    ("2026-09-26", "Survey", "Neha Gupta", "Love the faster search. Checkout payment errors are frustrating though, please fix them soon."),
    ("2026-09-27", "Support Ticket", "Karan Patel", "Search is much faster now, thanks. But checkout payment errors on UPI are happening for my team as well."),
    ("2026-09-28", "Email", "Meera Joshi (Zenith Retail)", "Search improved a lot and we are staying for now. Payment failures at checkout are our new top concern."),
]


def post(item):
    date, channel, customer, text = item
    payload = json.dumps({
        "date": date,
        "channel": channel,
        "customer": customer,
        "feedback": text,
    }).encode("utf-8")

    req = urllib.request.Request(
        URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


if __name__ == "__main__":
    for i, item in enumerate(DATA, start=1):
        try:
            result = post(item)
            status = "OK" if result.get("success") else "FAILED: " + str(result.get("error"))
        except Exception as e:
            status = "ERROR: " + repr(e)
        print(f"[{i}/{len(DATA)}] {item[0]} {item[1]} - {status}")
        time.sleep(2)

    print("Done.")
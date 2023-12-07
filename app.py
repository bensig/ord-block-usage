from flask import Flask, jsonify, request, render_template
import requests

app = Flask(__name__)
progress = {}


def get_inscriptions(block_number):
    global progress
    url = f"https://ord.zuexeuz.net/inscriptions/block/{block_number}"
    headers = {"Accept": "application/json", "User-Agent": ""}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        inscriptions = response.json().get("inscriptions", [])
        progress[block_number] = {"total": len(inscriptions), "fetched": 0}
        print(f"Found {len(inscriptions)} inscriptions")
        return inscriptions
    else:
        print(f"Failed to fetch inscriptions: Status code {response.status_code}")
        return []


def get_block_size(block_number):
    url = f"https://mempool.space/api/block-height/{block_number}"
    response = requests.get(url)
    if response.status_code == 200:
        block_hash = response.text.strip()
        block_url = f"https://mempool.space/api/block/{block_hash}"
        block_response = requests.get(block_url)
        if block_response.status_code == 200:
            block_data = block_response.json()
            return block_data.get("size", 0)
    return 0


def get_inscription_length(inscription_id, block_number):
    print(f"Fetching length for inscription ID: {inscription_id}")
    global progress
    url = f"https://ord.zuexeuz.net/inscription/{inscription_id}"
    headers = {"Accept": "application/json", "User-Agent": ""}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        length = response.json().get("content_length", 0)
        print(f"Inscription length: {length}")
        progress[block_number]["fetched"] += 1
        return length
    else:
        print(f"Failed to fetch inscription length: Status code {response.status_code}")
        return 0


@app.route("/api/total-size/<int:block_number>", methods=["GET"])
def total_size(block_number):
    global progress
    inscriptions = get_inscriptions(block_number)
    total_inscription_size = sum(
        get_inscription_length(inscription_id, block_number)
        for inscription_id in inscriptions
    )
    block_size = get_block_size(block_number)
    ordinal_percentage = (
        (total_inscription_size / block_size * 100) if block_size > 0 else 0
    )
    return jsonify(
        {
            "totalSize": total_inscription_size,
            "blockSize": block_size,
            "ordinalPercentage": ordinal_percentage,
        }
    )


@app.route("/api/progress/<int:block_number>", methods=["GET"])
def get_progress(block_number):
    global progress
    return jsonify(progress.get(block_number, {"total": 0, "fetched": 0}))


@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")  # Allows all domains
    return response


@app.route("/")
def index():
    return render_template("paper.html")


if __name__ == "__main__":
    app.run(debug=True)

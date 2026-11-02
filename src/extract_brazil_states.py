
import json
import time
from pathlib import Path

import requests

API_URL = "https://brasilapi.com.br/api/ibge/uf/v1"

OUTPUT_DIR = Path("data/bronze/api")
OUTPUT_FILE = OUTPUT_DIR / "brazil_states.json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def fetch_states():
    for attempt in range(1, 4):
        try:
            response = requests.get(API_URL, timeout=30)
            response.raise_for_status()

            states = response.json()

            if not isinstance(states, list) or not states:
                raise ValueError("Unexpected or empty API response")

            required_fields = {"id", "sigla", "nome", "regiao"}

            for state in states:
                missing = required_fields - state.keys()
                if missing:
                    raise ValueError(
                        f"Missing fields in API response: {missing}"
                    )

            return states

        except (requests.RequestException, ValueError) as error:
            print(f"Attempt {attempt} failed: {error}")

            if attempt == 3:
                raise

            time.sleep(2 ** attempt)


if __name__ == "__main__":
    states = fetch_states()

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(states, file, ensure_ascii=False, indent=2)

    print("Brazilian states extracted:", len(states))
    print("Output file:", OUTPUT_FILE)

    print("\nSample states:")
    for state in states[:5]:
        print(
            state["sigla"],
            state["nome"],
            state["regiao"]
        )

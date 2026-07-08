import argparse
import os
from streamlit import config, App
import uvicorn


def parse_env_value(value: str):
    v = value.strip()

    if v.lower() in ("true", "false"):
        return v.lower() == "true"

    if v.isdigit():
        return int(v)
    return v


def env_to_config_key(env_key: str) -> str:
    key = env_key[10:].lower()
    parts = key.split("_")
    section = parts[0]
    option = parts[1:]

    option_camel_case = option[0] + "".join(w.capitalize() for w in option[1:])

    if option_camel_case == "enableCors":
        option_camel_case = "enableCORS"

    return f"{section}.{option_camel_case}"


def apply_streamlit_env(prefix="STREAMLIT_"):

    for env_key, env_value in os.environ.items():
        if not env_key.startswith(prefix):
            continue

        config_key = env_to_config_key(env_key)
        value = parse_env_value(env_value)

        try:
            config.set_option(config_key, value)
        except Exception as e:
            print(e)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--socket",
        default="",
        help="Path to a unix socket to bind.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host address to bind when no socket is used.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="TCP port to bind when no socket is used.",
    )
    args = parser.parse_args()

    apply_streamlit_env()

    config.set_option(
        "theme.font",
        "Montserrat:https://processintel.org/api/font/montserrat/font.css",
    )
    config.set_option(
        "theme.sidebar.font",
        "Montserrat:https://processintel.org/api/font/montserrat/font.css",
    )

    config.set_option(
        "theme.light.font",
        "Montserrat:https://processintel.org/api/font/montserrat/font.css",
    )
    config.set_option(
        "theme.light.sidebar.font",
        "Montserrat:https://processintel.org/api/font/montserrat/font.css",
    )

    config.set_option(
        "theme.dark.font",
        "Montserrat:https://processintel.org/api/font/montserrat/font.css",
    )
    config.set_option(
        "theme.dark.sidebar.font",
        "Montserrat:https://processintel.org/api/font/montserrat/font.css",
    )

    app_path = os.path.join(os.path.dirname(__file__), "streamlit_app.py")
    app = App(app_path)

    if args.socket:
        uvicorn.run(
            app,
            uds=args.socket,
            ws_ping_interval=30,
            ws_ping_timeout=300,
        )
    else:
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            ws_ping_interval=30,
            ws_ping_timeout=300,
        )


if __name__ == "__main__":
    main()

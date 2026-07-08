from __future__ import annotations

import json

from foresight.demo.scenarios import SCENARIOS
from foresight.main import ForesightPipeline


def main() -> None:
    try:
        import streamlit as st  # type: ignore
    except Exception:
        print("Streamlit is not installed. Use: python -m foresight.ui.demo_cli --fake --pybullet-direct")
        return

    st.set_page_config(page_title="Foresight PM Demo", layout="wide")
    st.title("Foresight: physical world model safety gate")
    pipeline = ForesightPipeline(fast_mode=True)
    scene = pipeline.get_scene()
    st.subheader("Camera/source status")
    st.write("Fake / Limelight / YOLO / Kaggle are modular. Current: fake offline scene.")
    st.subheader("Scene graph")
    st.json(scene.model_dump(by_alias=True))
    choice = st.selectbox("Fallback scenarios", list(SCENARIOS.keys()))
    command = st.text_input("Command", value=SCENARIOS[choice])
    if st.button("Evaluate"):
        result = pipeline.evaluate_command(command)
        c1, c2 = st.columns(2)
        c1.subheader("Parsed intent")
        c1.json(result.parsed.model_dump(by_alias=True))
        c2.subheader("Planning result")
        c2.json(result.planning.model_dump())
        st.subheader("Simulation verdict")
        st.json(result.simulation.model_dump() if result.simulation else None)
        st.subheader("Final safety decision")
        st.json(result.safety.model_dump())
        st.code(json.dumps(result.model_dump(), ensure_ascii=False, indent=2)[:4000])


if __name__ == "__main__":
    main()

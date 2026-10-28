import os
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

try:
    from google import genai
except ImportError:
    genai = None

st.set_page_config(page_title="Interrupt Priority Scheduling Simulator", page_icon="⚡", layout="wide")
st.title("⚡ Intelligent Interrupt Management and Priority Scheduling System")
st.caption("Educational simulation of interrupt requests, scheduling, execution history, and AI-assisted analysis.")

PRIORITY_VALUE = {"Low": 1, "Medium": 2, "High": 3}
DEFAULT_SOURCES = {
    "Timer": {"priority": "High", "execution_time": 4},
    "Communication": {"priority": "Medium", "execution_time": 6},
    "Keyboard": {"priority": "Low", "execution_time": 3},
    "Peripheral": {"priority": "Medium", "execution_time": 5},
}

def schedule_requests(requests, policy="Priority (non-preemptive)"):
    """All requests are treated as pending at time zero; execution is non-preemptive."""
    if policy == "FCFS":
        ordered = sorted(requests, key=lambda r: r["arrival_order"])
    elif policy == "Priority (non-preemptive)":
        ordered = sorted(requests, key=lambda r: (-PRIORITY_VALUE[r["priority"]], r["arrival_order"]))
    else:
        raise ValueError("Unknown scheduling policy.")
    clock, results = 0, []
    for req in ordered:
        start = clock
        finish = start + req["execution_time"]
        results.append({**req, "start_time": start, "completion_time": finish,
                        "waiting_time": start, "response_time": start,
                        "turnaround_time": finish})
        clock = finish
    return results

def summarize(results):
    if not results:
        return {"average_waiting": 0.0, "average_response": 0.0,
                "average_turnaround": 0.0, "total_time": 0}
    n = len(results)
    return {
        "average_waiting": sum(r["waiting_time"] for r in results) / n,
        "average_response": sum(r["response_time"] for r in results) / n,
        "average_turnaround": sum(r["turnaround_time"] for r in results) / n,
        "total_time": max(r["completion_time"] for r in results),
    }

def ai_explanation(requests, priority_results, fcfs_results, selected_policy):
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    pstats, fstats = summarize(priority_results), summarize(fcfs_results)
    prompt = f"""
You are an educational microprocessor interrupt scheduling assistant.
Explain only from these simulation results. This is a simplified non-preemptive
software simulation, not real hardware. All requests are treated as pending at
time zero; execution times are arbitrary simulation units.
Requests: {requests}
Priority order: {[r['source'] for r in priority_results]}
FCFS order: {[r['source'] for r in fcfs_results]}
Priority average waiting: {pstats['average_waiting']:.2f}
FCFS average waiting: {fstats['average_waiting']:.2f}
Priority average turnaround: {pstats['average_turnaround']:.2f}
FCFS average turnaround: {fstats['average_turnaround']:.2f}
Explain the order, compare the metrics, mention starvation/trade-offs, and give
a recommendation only if supported by these results. Keep it student-friendly.
"""
    if not api_key or genai is None:
        return (
            f"**Rule-based explanation (Gemini not configured).** The selected policy is "
            f"{selected_policy}. Priority order: {' → '.join(r['source'] for r in priority_results)}. "
            f"FCFS order: {' → '.join(r['source'] for r in fcfs_results)}. "
            f"Average waiting time is {pstats['average_waiting']:.2f} for priority scheduling "
            f"and {fstats['average_waiting']:.2f} for FCFS. Priority scheduling serves high-priority "
            "requests first, but low-priority requests can wait longer. Add GEMINI_API_KEY in "
            "Render Environment settings to enable Gemini-generated explanations."
        )
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text or "The AI model returned an empty response."
    except Exception as exc:
        return f"AI explanation failed; simulator results are still available. Details: {exc}"

st.sidebar.header("Simulation settings")
policy = st.sidebar.selectbox("Scheduling policy", ["Priority (non-preemptive)", "FCFS"])
st.sidebar.info("Simplified model: all displayed requests are pending at time zero; execution is non-preemptive.")

if "requests" not in st.session_state:
    st.session_state.requests = []
if "next_id" not in st.session_state:
    st.session_state.next_id = 1
if "arrival_counter" not in st.session_state:
    st.session_state.arrival_counter = 1

st.subheader("1. Configure interrupt sources")
source_cols = st.columns(4)
settings = {}
for idx, (name, cfg) in enumerate(DEFAULT_SOURCES.items()):
    with source_cols[idx]:
        st.markdown(f"**{name}**")
        priority = st.selectbox(f"{name} priority", ["High", "Medium", "Low"],
            index=["High", "Medium", "Low"].index(cfg["priority"]), key=f"priority_{name}")
        execution_time = st.number_input(f"{name} execution time", min_value=1, max_value=1000,
            value=cfg["execution_time"], step=1, key=f"time_{name}")
        settings[name] = {"priority": priority, "execution_time": int(execution_time)}

source = st.selectbox("Interrupt source to add", list(DEFAULT_SOURCES.keys()))
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("＋ Generate interrupt", type="primary", use_container_width=True):
        cfg = settings[source]
        st.session_state.requests.append({
            "request_id": st.session_state.next_id, "source": source,
            "priority": cfg["priority"], "execution_time": cfg["execution_time"],
            "arrival_order": st.session_state.arrival_counter,
        })
        st.session_state.next_id += 1
        st.session_state.arrival_counter += 1
        st.rerun()
with c2:
    if st.button("Load example requests", use_container_width=True):
        st.session_state.requests = []
        for name, priority, duration in [
            ("Keyboard", "Low", 3), ("Timer", "High", 4), ("Communication", "Medium", 6)
        ]:
            st.session_state.requests.append({
                "request_id": st.session_state.next_id, "source": name,
                "priority": priority, "execution_time": duration,
                "arrival_order": st.session_state.arrival_counter,
            })
            st.session_state.next_id += 1
            st.session_state.arrival_counter += 1
        st.rerun()
with c3:
    if st.button("Clear queue", use_container_width=True):
        st.session_state.requests = []
        for key in ["last_priority", "last_fcfs", "last_selected", "last_policy"]:
            st.session_state.pop(key, None)
        st.rerun()

requests = st.session_state.requests
st.subheader("2. Pending interrupt queue")
if requests:
    pending = pd.DataFrame(requests)
    pending["rank"] = pending["priority"].map(PRIORITY_VALUE)
    st.dataframe(pending.sort_values(["rank", "arrival_order"], ascending=[False, True])[
        ["request_id", "source", "priority", "execution_time", "arrival_order"]],
        use_container_width=True, hide_index=True)
else:
    st.info("Generate requests or load the example to begin.")

st.subheader("3. Run scheduler and compare policies")
if st.button("Run simulation", type="primary", disabled=not requests):
    st.session_state.last_priority = schedule_requests(requests, "Priority (non-preemptive)")
    st.session_state.last_fcfs = schedule_requests(requests, "FCFS")
    st.session_state.last_selected = schedule_requests(requests, policy)
    st.session_state.last_policy = policy

if "last_selected" in st.session_state:
    pr = st.session_state.last_priority
    fc = st.session_state.last_fcfs
    selected = st.session_state.last_selected
    selected_policy = st.session_state.last_policy
    stats = summarize(selected)
    cols = st.columns(4)
    cols[0].metric("Requests processed", len(selected))
    cols[1].metric("Average waiting", f"{stats['average_waiting']:.2f}")
    cols[2].metric("Average turnaround", f"{stats['average_turnaround']:.2f}")
    cols[3].metric("Total simulation time", f"{stats['total_time']}")

    st.markdown(f"### Execution history — {selected_policy}")
    df = pd.DataFrame(selected)
    st.dataframe(df[["request_id", "source", "priority", "execution_time",
        "start_time", "completion_time", "waiting_time", "turnaround_time"]],
        use_container_width=True, hide_index=True)

    st.markdown("### Execution timeline")
    fig, ax = plt.subplots(figsize=(10, max(2.5, 0.65 * len(selected))))
    for row, item in enumerate(selected):
        ax.barh(row, item["execution_time"], left=item["start_time"], height=0.55)
        ax.text(item["start_time"] + item["execution_time"] / 2, row, item["source"],
                ha="center", va="center", fontsize=9)
    ax.set_yticks(range(len(selected)))
    ax.set_yticklabels([f"Request {r['request_id']}" for r in selected])
    ax.set_xlabel("Simulation time units")
    ax.set_title("Interrupt execution timeline")
    ax.grid(axis="x", alpha=0.3)
    st.pyplot(fig)
    plt.close(fig)

    st.markdown("### Policy comparison")
    pstats, fstats = summarize(pr), summarize(fc)
    comparison = pd.DataFrame([
        {"Policy": "Priority (non-preemptive)", "Order": " → ".join(r["source"] for r in pr),
         "Average waiting": round(pstats["average_waiting"], 2),
         "Average turnaround": round(pstats["average_turnaround"], 2)},
        {"Policy": "FCFS", "Order": " → ".join(r["source"] for r in fc),
         "Average waiting": round(fstats["average_waiting"], 2),
         "Average turnaround": round(fstats["average_turnaround"], 2)},
    ])
    st.dataframe(comparison, use_container_width=True, hide_index=True)

    st.markdown("### 4. Agent analysis")
    st.write("The agent uses the scheduler outputs and computed metrics to explain its recommendation.")
    if st.button("Analyze queue with AI agent"):
        with st.spinner("Analyzing queue and comparing policies..."):
            explanation = ai_explanation(requests, pr, fc, selected_policy)
        st.markdown(explanation)

    st.download_button("Download execution history (CSV)",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="interrupt_execution_history.csv", mime="text/csv")

st.divider()
st.caption("Educational software simulation only; it does not control or measure real processor hardware.")

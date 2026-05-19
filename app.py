"""
Family Routine Board — a simple Streamlit app for family morning/evening routines.
"""

import json
from datetime import date
from pathlib import Path

import streamlit as st

# --- File paths ---
DATA_FILE = Path(__file__).parent / "routines.json"

# Common emoji choices for steps (parent can pick from this list)
EMOJI_OPTIONS = [
    "🛏️", "🪥", "👕", "🍳", "🥣", "🎒", "👟", "🧸",
    "📚", "🚿", "🧦", "🧴", "🐕", "🌞", "🌙", "⭐",
    "🎵", "🚗", "🏫", "🧹", "💊", "💧", "🍎", "🎮",
]


def load_data():
    """Load routines and today's progress from JSON."""
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"routines": {}, "progress": {}}


def save_data(data):
    """Save routines and progress to JSON."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def today_key():
    """Today's date as a string key for progress tracking."""
    return date.today().isoformat()


def get_progress(data, routine_id):
    """Get which steps are done today for a routine."""
    day = today_key()
    return data.get("progress", {}).get(day, {}).get(routine_id, [])


def set_step_done(data, routine_id, step_index, done):
    """Mark a step done or not done for today."""
    day = today_key()
    if "progress" not in data:
        data["progress"] = {}
    if day not in data["progress"]:
        data["progress"][day] = {}
    if routine_id not in data["progress"][day]:
        data["progress"][day][routine_id] = []

    done_list = data["progress"][day][routine_id]
    if done and step_index not in done_list:
        done_list.append(step_index)
    elif not done and step_index in done_list:
        done_list.remove(step_index)
    save_data(data)


def reset_routine_today(data, routine_id):
    """Clear today's progress for one routine."""
    day = today_key()
    if day in data.get("progress", {}) and routine_id in data["progress"][day]:
        data["progress"][day][routine_id] = []
        save_data(data)


def init_session():
    """Set up session state on first run."""
    if "data" not in st.session_state:
        st.session_state.data = load_data()
    if "screen" not in st.session_state:
        st.session_state.screen = "home"
    if "active_routine_id" not in st.session_state:
        st.session_state.active_routine_id = None
    if "edit_routine_id" not in st.session_state:
        st.session_state.edit_routine_id = None


def go_home():
    st.session_state.screen = "home"
    st.session_state.active_routine_id = None


def show_stars(total_steps, done_indices):
    """Show progress as stars at the top."""
    if total_steps == 0:
        st.caption("No steps yet — add some in Edit mode.")
        return
    done_count = len(done_indices)
    stars = "⭐" * done_count + "☆" * (total_steps - done_count)
    st.markdown(
        f"<h2 style='text-align:center; font-size:2.5rem;'>{stars}</h2>",
        unsafe_allow_html=True,
    )
    st.caption(f"{done_count} of {total_steps} done today")


def screen_home():
    """Home screen: pick a routine or manage routines."""
    st.title("🏠 Family Routine Board")
    st.markdown("Choose a routine to start, or create a new one.")

    routines = st.session_state.data.get("routines", {})
    routine_ids = list(routines.keys())

    if routine_ids:
        st.subheader("Your routines")
        for rid in routine_ids:
            routine = routines[rid]
            step_count = len(routine.get("steps", []))
            done = get_progress(st.session_state.data, rid)
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"### {routine['name']}")
                st.caption(f"{len(done)} / {step_count} done today")
            with col2:
                if st.button("▶️ Start", key=f"start_{rid}", use_container_width=True):
                    st.session_state.active_routine_id = rid
                    st.session_state.screen = "play"
                    st.rerun()
            with col3:
                if st.button("✏️ Edit", key=f"edit_{rid}", use_container_width=True):
                    st.session_state.edit_routine_id = rid
                    st.session_state.screen = "edit"
                    st.rerun()
            st.divider()
    else:
        st.info("No routines yet. Create your first one below!")

    st.subheader("➕ Create new routine")
    with st.form("create_routine"):
        new_name = st.text_input("Routine name", placeholder="Morning routine")
        submitted = st.form_submit_button("Create routine")
        if submitted:
            if not new_name.strip():
                st.error("Please enter a name.")
            else:
                rid = new_name.strip().lower().replace(" ", "_")
                # Make sure id is unique
                base_rid = rid
                n = 1
                while rid in routines:
                    rid = f"{base_rid}_{n}"
                    n += 1
                st.session_state.data["routines"][rid] = {
                    "name": new_name.strip(),
                    "steps": [],
                }
                save_data(st.session_state.data)
                st.session_state.edit_routine_id = rid
                st.session_state.screen = "edit"
                st.rerun()


def screen_edit():
    """Edit a routine: add/remove steps and pick emojis."""
    rid = st.session_state.edit_routine_id
    data = st.session_state.data
    if not rid or rid not in data.get("routines", {}):
        go_home()
        st.rerun()
        return

    routine = data["routines"][rid]

    if st.button("← Back to home"):
        go_home()
        st.rerun()

    st.title(f"✏️ Edit: {routine['name']}")

    # Rename routine
    with st.form("rename_routine"):
        new_name = st.text_input("Routine name", value=routine["name"])
        if st.form_submit_button("Save name"):
            routine["name"] = new_name.strip() or routine["name"]
            save_data(data)
            st.success("Name saved!")
            st.rerun()

    st.subheader("Steps (in order)")
    steps = routine.get("steps", [])

    if not steps:
        st.caption("No steps yet. Add one below.")

    for i, step in enumerate(steps):
        col_emoji, col_text, col_del = st.columns([1, 4, 1])
        with col_emoji:
            st.markdown(f"## {step.get('emoji', '⭐')}")
        with col_text:
            st.markdown(f"**{i + 1}. {step.get('label', 'Step')}**")
        with col_del:
            if st.button("🗑️", key=f"del_{rid}_{i}", help="Delete this step"):
                steps.pop(i)
                routine["steps"] = steps
                save_data(data)
                st.rerun()

    st.subheader("Add a step")
    with st.form("add_step", clear_on_submit=True):
        label = st.text_input("Step name", placeholder="Brush teeth")
        emoji = st.selectbox("Emoji icon", EMOJI_OPTIONS)
        if st.form_submit_button("Add step"):
            if not label.strip():
                st.error("Please enter a step name.")
            else:
                steps.append({"label": label.strip(), "emoji": emoji})
                routine["steps"] = steps
                save_data(data)
                st.rerun()

    if steps and st.button("▶️ Start this routine"):
        st.session_state.active_routine_id = rid
        st.session_state.screen = "play"
        st.rerun()

    if st.button("🗑️ Delete entire routine", type="secondary"):
        del data["routines"][rid]
        save_data(data)
        go_home()
        st.rerun()


def screen_play():
    """Child-friendly view: big cards and Done buttons."""
    rid = st.session_state.active_routine_id
    data = st.session_state.data
    if not rid or rid not in data.get("routines", {}):
        go_home()
        st.rerun()
        return

    routine = data["routines"][rid]
    steps = routine.get("steps", [])

    col_back, col_reset = st.columns([1, 1])
    with col_back:
        if st.button("← Home"):
            # Progress is already saved in JSON — switching routines keeps it
            go_home()
            st.rerun()
    with col_reset:
        if st.button("🔄 Reset for tomorrow", help="Clear today's checkmarks"):
            reset_routine_today(data, rid)
            st.session_state.data = load_data()
            st.rerun()

    st.title(routine["name"])

    done_indices = get_progress(data, rid)
    show_stars(len(steps), done_indices)

    if not steps:
        st.warning("This routine has no steps yet. Go to Edit to add some.")
        return

    # Routine picker while playing (switch without losing progress)
    routine_names = {
        data["routines"][r]["name"]: r
        for r in data["routines"]
    }
    current_name = routine["name"]
    picked = st.selectbox(
        "Switch routine",
        options=list(routine_names.keys()),
        index=list(routine_names.keys()).index(current_name),
    )
    if routine_names[picked] != rid:
        st.session_state.active_routine_id = routine_names[picked]
        st.rerun()

    st.markdown("---")

    # Large cards — any order; tap Done on any step
    for i, step in enumerate(steps):
        is_done = i in done_indices
        emoji = step.get("emoji", "⭐")
        label = step.get("label", "Step")

        border = "#4CAF50" if is_done else "#E0E0E0"
        bg = "#E8F5E9" if is_done else "#FFFFFF"
        opacity = "0.85" if is_done else "1"

        card_html = f"""
        <div style="margin-bottom: 1rem;">
        <div style="
            border: 4px solid {border};
            border-radius: 20px;
            padding: 1.5rem;
            background: {bg};
            text-align: center;
            opacity: {opacity};
        ">
            <div style="font-size: 4rem;">{emoji}</div>
            <div style="font-size: 1.8rem; font-weight: bold; margin: 0.5rem 0;">
                {label}
            </div>
        </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if not is_done:
                if st.button("✅ Done!", key=f"done_{rid}_{i}", use_container_width=True):
                    set_step_done(data, rid, i, True)
                    st.session_state.data = load_data()
                    st.rerun()
        with btn_col2:
            if is_done:
                if st.button("↩️ Undo", key=f"undo_{rid}_{i}", use_container_width=True):
                    set_step_done(data, rid, i, False)
                    st.session_state.data = load_data()
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)


def main():
    st.set_page_config(
        page_title="Family Routine Board",
        page_icon="🏠",
        layout="wide",
    )

    # Friendly, large touch targets
    st.markdown(
        """
        <style>
        .stButton > button {
            font-size: 1.2rem;
            padding: 0.6rem 1.2rem;
            min-height: 3rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    init_session()

    screen = st.session_state.screen
    if screen == "home":
        screen_home()
    elif screen == "edit":
        screen_edit()
    elif screen == "play":
        screen_play()
    else:
        go_home()
        screen_home()


if __name__ == "__main__":
    main()

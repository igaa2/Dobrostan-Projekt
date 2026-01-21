import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from loguru import logger
from src.utils.utils import get_project_root, load_md
from src.utils.data_classes import Variable, SessionStatePrefix


def configurate_page() -> None:
    """Set Streamlit page configuration."""
    st.set_page_config(
        page_title="Dobrostan Województw Polski",
        page_icon="📊",
        layout="wide",  # page elements use the entire screen width
        initial_sidebar_state="expanded",
        menu_items={"About": load_md(get_project_root() / "streamlit" / "about.md")},
    )
    logger.info("Streamlit page configured.")


def configure_sidebar() -> None:
    """Configure the Streamlit sidebar with project information."""
    st.sidebar.title("⚙️ Ustawienia zmiennych")
    st.sidebar.caption("Waga | Typ (📈 stymulanta / 📉 destymulanta)")
    st.sidebar.markdown(
        "Ustal ważność zmiennych i wskaż, czy ich wpływ na wynik jest pozytywny (stymulanta) czy negatywny (destymulanta)."
    )
    st.sidebar.markdown("---")
    logger.info("Sidebar configured.")


def configurate_main() -> None:
    st.title("📊 Dobrostan Województw Polski")
    st.markdown("---")


def ensure_session_state(variables: list[Variable]) -> None:
    """Inicjalizuje brakujące pary klucz-wartość w session_state dla wszystkich zmiennych."""
    for variable in variables:
        st.session_state.setdefault(
            SessionStatePrefix.SLIDER.key(variable.variable_id), variable.weight
        )

        # st.session_state.setdefault(
        #     SessionStatePrefix.SLIDER_TMP.key(variable.variable_id), variable.weight
        # )

        st.session_state.setdefault(
            SessionStatePrefix.TOGGLE.key(variable.variable_id), variable.stimulant
        )

        # st.session_state.setdefault(
        #     SessionStatePrefix.TOGGLE_TMP.key(variable.variable_id), variable.weight
        # )


def warn_if_all_sliders_zero() -> bool:
    """
    Sprawdza, czy wszystkie klucze dla suwaków mają wartość 0.
    Jeśli tak — wyświetla ostrzeżenie w Streamlit.

    Zwraca:
        True - jeśli wszystkie wagi == 0
        False - w przeciwnym razie
    """
    weights = [
        v
        for k, v in st.session_state.items()
        if k.startswith(SessionStatePrefix.SLIDER.value)
        # if k.startswith(SessionStatePrefix.SLIDER_TMP.value)
    ]

    if weights and all(v == 0 for v in weights):
        st.warning(
            "⚠️ Wszystkie wagi mają wartość 0. "
            "Nie można porównać jednostek — ustaw co najmniej jedną wagę większą od 0."
        )
        return True

    return False


def generate_slider(
    container: DeltaGenerator, session_state_key: str, name: str
) -> float:
    """Tworzy suwak od 0% do 100% w pasku bocznym Streamlit."""
    return container.slider(
        label=name,
        min_value=0,
        max_value=100,
        step=1,
        format="%d%%",
        key=session_state_key,
        label_visibility="collapsed",
    )


def generate_toggle(container: DeltaGenerator, session_state_key: str) -> bool:
    """Tworzy przełącznik na destymulantę w pasku bocznym Streamlit."""
    return container.toggle(
        label="📉",
        key=session_state_key,
        label_visibility="visible",
        help="OFF = stymulanta, ON = destymulanta",
    )


def generate_sliders_and_toggles_for_variables(
    variables: list[Variable], validation: dict[int, str]
) -> None:
    """Generates the sidebar with sliders and toggles for each variable."""
    for variable in variables:
        validation_status = validation[variable.variable_id]
        st.sidebar.markdown(f"**{variable.name}**")
        st.sidebar.markdown(f"Status walidacji: {validation_status}")

        col_slider, col_toggle = st.sidebar.columns([2, 1])

        generate_slider(
            container=col_slider,
            session_state_key=SessionStatePrefix.SLIDER.key(variable.variable_id),
            # session_state_key=SessionStatePrefix.SLIDER_TMP.key(variable.variable_id),
            name=variable.name,
        )

        generate_toggle(
            container=col_toggle,
            session_state_key=SessionStatePrefix.TOGGLE.key(variable.variable_id),
            # session_state_key=SessionStatePrefix.TOGGLE_TMP.key(variable.variable_id),
        )

    st.sidebar.markdown("---")
    logger.info("Sliders and toggles generated in sidebar.")


# def activate_variables_settings(variables: list[Variable]):
#     """Finalizuje ustawienia wag i stymulant zgromadzone w tymczasowych zmiennych."""
#     for variable in variables:
#         st.session_state[SessionStatePrefix.SLIDER.key(variable.variable_id)] = (
#             st.session_state[SessionStatePrefix.SLIDER_TMP.key(variable.variable_id)]
#         )

#         st.session_state[SessionStatePrefix.TOGGLE.key(variable.variable_id)] = (
#             st.session_state[SessionStatePrefix.TOGGLE_TMP.key(variable.variable_id)]
#         )


def reset_session_state_by_prefix(prefix: str) -> None:
    """Usuwa klucze rozpoczynające się od prefix w słowniku session_state."""
    for key in list(st.session_state.keys()):
        if key.startswith(prefix):
            del st.session_state[key]

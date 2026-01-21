from loguru import logger
import streamlit as st

from src.utils.data_classes import Variable, SessionStatePrefix, DataParams
from src.utils.utils import get_project_root, load_md, load_yaml
from src.streamlit.configuration_utils import (
    configurate_page,
    configure_sidebar,
    configurate_main,
    ensure_session_state,
    generate_sliders_and_toggles_for_variables,
    reset_session_state_by_prefix,
    # activate_variables_settings,
    warn_if_all_sliders_zero,
)
from src.streamlit.data_utils import (
    fetch_most_recent_year_data_for_variables,
    normalize_per_variable,
    validate_and_extract_validation,
)
from src.streamlit.plots import (
    create_map,
    create_horizontal_barplot_with_mean_line,
    create_radar,
)
from src.composite_index.validator import VariableValidator
from src.composite_index.copras import (
    calculate_copras,
    calculate_hybrid_weights,
)


def main():
    root = get_project_root()
    config = load_yaml(root / "config.yaml")

    data_params = DataParams.from_dict(config["data"]["params"])
    variables = [Variable.from_dict(dictionary=d) for d in config["data"]["variables"]]
    logger.info(
        f"Number of variables used: {len(variables)}. "
        f"Id of variables used: {[v.variable_id for v in variables]}. "
    )

    # ==================== POBRANIE DANYCH ====================

    df_oryginal = fetch_most_recent_year_data_for_variables(
        variables=variables,
        params=data_params,
        sleep_between_requests=0.5,
    )

    validation_infos, validation_cv = validate_and_extract_validation(df=df_oryginal)

    df_normalized = normalize_per_variable(df=df_oryginal)

    # ==================== KONFIGURACJA STRONY ====================

    configurate_page()

    # ==================== KONFIGURACJA PANELU BOCZNEGO ====================

    configure_sidebar()

    ensure_session_state(variables=variables)
    generate_sliders_and_toggles_for_variables(
        variables=variables, validation=validation_infos
    )

    if warn_if_all_sliders_zero():
        st.stop()

    # Przyciski resetów
    col_reset_sliders, col_reset_toggles = st.sidebar.columns(2)

    with col_reset_sliders:
        if st.button(
            f"🔄⚖️ Resetuj {SessionStatePrefix.SLIDER.value}",
            use_container_width=True,
        ):
            reset_session_state_by_prefix(SessionStatePrefix.SLIDER.value)
            # reset_session_state_by_prefix(SessionStatePrefix.SLIDER_TMP.value)
            st.rerun()

    with col_reset_toggles:
        if st.button(
            f"🔄📉 Resetuj {SessionStatePrefix.TOGGLE.value}",
            use_container_width=True,
        ):
            reset_session_state_by_prefix(SessionStatePrefix.TOGGLE.value)
            # reset_session_state_by_prefix(SessionStatePrefix.TOGGLE_TMP.value)
            st.rerun()

    # if st.sidebar.button("✅ Zastosuj konfigurację", use_container_width=True):
    #     activate_variables_settings(variables)
    #     st.session_state["flag"] = True
    #     st.rerun()

    # ==================== PRZELICZENIE WSKAŹNIKA ====================

    # flag = st.session_state.get("flag", True)
    # if flag:
    # flag = False
    # indent zrobic do końca
    weights = SessionStatePrefix.extract_sliders_keys(dictionary=st.session_state)
    stimulants = SessionStatePrefix.extract_toggles_keys(dictionary=st.session_state)

    df_index = calculate_copras(
        df=df_normalized,
        weights=calculate_hybrid_weights(
            validation_cv=validation_cv, slider_weights=weights
        ),
        stimulants=stimulants,
    )

    # ==================== KONFIGURACJA PANELU GŁÓWNEGO ====================

    configurate_main()

    col_map, col_barplot = st.columns([2, 3])

    with col_map:
        fig_map = create_map(
            df=df_index,
            value_col_name="value",
            unit_col_name="unit_name",
            value_label="Wskaźnik dobrostanu",
        )
        st.plotly_chart(fig_map, width="stretch")

    with col_barplot:
        fig_barplot = create_horizontal_barplot_with_mean_line(
            df=df_index,
            value_col_name="value",
            value_label="Wskaźnik dobrostanu",
            unit_col_name="unit_name",
            unit_label="Województwo",
        )
        st.plotly_chart(fig_barplot, width="stretch")

    # Wybór województw do porównania
    st.subheader("Porównanie województw - dane po normalizacji wektorowej")

    unit_names_chosen = st.multiselect(
        "Wybierz województwa do porównania",
        options=df_index["unit_name"],
        default=df_index["unit_name"].head(n=3),
        max_selections=5,  # Limit dla czytelności
    )

    if unit_names_chosen:
        fig_radar = create_radar(
            df=df_normalized,
            value_col_name="value",
            variable_col_name="name",
            unit_col_name="unit_name",
            chosen_units=unit_names_chosen,
        )
        st.plotly_chart(fig_radar, width="stretch")
    else:
        st.warning("Wybierz przynajmniej jedno województwo.")


if __name__ == "__main__":
    main()

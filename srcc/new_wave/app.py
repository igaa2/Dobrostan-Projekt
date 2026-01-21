from loguru import logger
import streamlit as st

from srcc.new_wave.data_classes import Variable, SessionStatePrefix, DataParams
from srcc.utils.utils import get_project_root, load_md, load_yaml
from srcc.new_wave.dashboard.configuration_utils import (
    configurate_page,
    configure_sidebar,
    configurate_main,
    ensure_session_state,
    generate_sliders_and_toggles_for_variables,
    reset_session_state_by_prefix,
    warn_if_all_sliders_zero,
)
from srcc.new_wave.bdl.bdl_utils import fetch_most_recent_year_data_for_variables
from srcc.new_wave.dashboard.plots import (
    create_map,
    create_horizontal_barplot_with_mean_line,
    create_radar,
)
from srcc.new_wave.composite_index.validator import VariableValidator
from srcc.new_wave.composite_index.normalizer import normalize_per_variable
from srcc.new_wave.composite_index.copras import calculate_copras, calculate_weights


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
        sleep_between_requests=1.0,
    )

    validation = VariableValidator().validate_dataframe(df=df_oryginal)
    validation_infos = {v.variable_id: v.validation_info() for v in validation}
    validation_cv = {v.variable_id: v.cv for v in validation}  # do wag

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
            on_click=reset_session_state_by_prefix,
            kwargs={"prefix": SessionStatePrefix.SLIDER.value},
        ):
            st.rerun()

    with col_reset_toggles:
        if st.button(
            f"🔄📉 Resetuj {SessionStatePrefix.TOGGLE.value}",
            use_container_width=True,
            on_click=reset_session_state_by_prefix,
            kwargs={"prefix": SessionStatePrefix.TOGGLE.value},
        ):
            st.rerun()

    # ==================== PRZELICZENIE WSKAŹNIKA ====================

    df_index = calculate_copras(
        df=df_normalized,
        weights=calculate_weights(validation_cv=validation_cv),
        destimulants={
            k.removeprefix(SessionStatePrefix.TOGGLE.value): v
            for k, v in st.session_state.items()
            if k.startswith(SessionStatePrefix.TOGGLE.value)
        },
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

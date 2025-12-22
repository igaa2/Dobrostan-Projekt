# Wskaźnik Kompozytowy Jakości Życia Polskich Województw (DobrostanPL) :shamrock:

## Spis treści
* [Charakterystyka oprogramowania](#charakterystyka-oprogramowania)
* [Prawa autorskie](#prawa-autorskie)
* [Specyfikacja wymagań](#specyfikacja-wymagań)
* [Architektura oprogramowania](#architektura-oprogramowania)
* [Testy](#testy)

## Charakterystyka oprogramowania
System `DobrostanPL` to narzędzie analityczne służące do oceny i porównywania jakości życia w polskich województwach. Aplikacja dynamicznie pobiera dane z publicznego API Banku Danych Lokalnych Głównego Urzędu Statystycznego (BDL GUS), co gwarantuje dostęp do oficjalnych danych statystycznych. Na ich podstawie generowane są rankingi oraz wizualizacje mapowe. Dobór zakresu czasowego danych następuje w oparciu o weryfikację metadanych poszczególnych zmiennych, co pozwala na pobranie wartości z najnowszego dostępnego roku. 

Głównym celem projektu jest dostarczenie użytkownikowi rzetelnej informacji o tym, gdzie w Polsce panują najlepsze warunki do życia, z uwzględnieniem spersonalizowanych kryteriów.

## Prawa autorskie
* **Autorzy oprogramowania:**
  - Iga Bochniak
  - Agnieszka Góral
  - Hanna Sopala
* **Licencja:** MIT

## Specyfikacja wymagań

*Wymagania funkcjonalne zdefiniowane w formie historyjek użytkownika (User Stories).*

### Moduł Danych i Obliczeń (Backend)

> **US-01:** Jako **Administrator Systemu**, chcę, aby aplikacja **automatycznie pobierała dane z API Banku Danych Lokalnych (GUS)**, aby wskaźniki opierały się na oficjalnych i najbardziej aktualnych statystykach.

> **US-02:** Jako **Analityk**, chcę, aby system **normalizował dane wejściowe (sprowadzał do wspólnej skali)**, aby możliwe było poprawne obliczenie wskaźnika kompozytowego dla różnych typów danych (np. zarobki w PLN i zanieczyszczenie w µg/m³).

### Moduł Interfejsu i Prezentacji (Frontend)

> **US-03:** Jako **Użytkownik Szukający Miejsca do Życia**, chcę **zobaczyć ranking powiatów posortowany według jakości życia**, aby szybko zidentyfikować najlepsze regiony do zamieszkania.

> **US-04:** Jako **Użytkownik**, chcę **mieć możliwość zmiany wag poszczególnych kryteriów (np. zwiększyć ważność "Bezpieczeństwa", a zmniejszyć "Ekonomii")**, aby obliczony wskaźnik kompozytowy odpowiadał moim osobistym preferencjom.

> **US-05:** Jako **Użytkownik**, chcę **zobaczyć wyniki na interaktywnej mapie Polski**, aby łatwiej ocenić rozkład jakości życia w interesującym mnie województwie.

> **US-06:** Jako **Użytkownik**, chcę **porównać dwa wybrane województwa w widoku "obok siebie"**, aby wyraźnie zobaczyć różnice w konkretnych składowych wskaźnika.

## Architektura oprogramowania

### Architektura rozwoju
*Stos technologiczny wykorzystywany podczas tworzenia oprogramowania.*

| Nazwa Technologii | Przeznaczenie | Wersja |
| :--- | :--- | :--- |
|  |  |  |
|  |  |  |
|  |  |  |
|  |  |  |

### Architektura uruchomieniowa
*Technologie wymagane do działania systemu w środowisku docelowym.*

| Nazwa Technologii | Przeznaczenie | Wersja |
| :--- | :--- | :--- |
|  |  |  |
|  |  |  |
|  |  |  |
|  |  |  |

## Testy

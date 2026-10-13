/**
 * @license
 * Copyright 2022 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * Global light/dark theme support.
 *
 * All color design tokens are defined on the `html` element in a single
 * globally injected stylesheet, rather than on each component's `:host`.
 * Because CSS custom properties inherit across shadow boundaries, every
 * Lit component (and any SVG/d3 element using `var(...)`) resolves tokens
 * from this sheet, and switching themes is as simple as toggling the
 * `lit-dark` class on `html`.
 *
 * The dark theme inverts the neutral / neutral-variant / minor tonal ramps
 * (which are used for chrome: backgrounds, text, borders, hover tints) while
 * leaving the brand and viz color ramps intact, since those encode data.
 */

/** Available app themes. */
export type Theme = 'light'|'dark';

/** Class set on `html` when the dark theme is active. */
export const DARK_THEME_CLASS = 'lit-dark';

/** LocalStorage key holding the user's explicit theme choice, if any. */
export const THEME_STORAGE_KEY = 'lit-theme';

/** ID of the injected global theme stylesheet. */
export const THEME_STYLE_ELEMENT_ID = 'lit-global-theme-styles';

/**
 * The chevron glyph used by `.dropdown` selects, as a data URI background
 * image. The fill color cannot reference a custom property from within the
 * URI, so the whole URI is exposed as a token and swapped per theme.
 */
const DROPDOWN_ARROW_SVG = (fill: string) =>
    `url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22${
        fill}%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E')`;

/**
 * Global theme sheet: palette tokens, semantic tokens, and their dark-mode
 * overrides. Injected into the document head by
 * `injectGlobalThemeStyles()`.
 */
export const GLOBAL_THEME_CSS = `
html {
  /* LIT Brand Palettes */
  --lit-cyea-50:  #EDFFFA;
  --lit-cyea-100: #CDF2FA;
  --lit-cyea-200: #AFE6DE;
  --lit-cyea-300: #7BCCCC;
  --lit-cyea-400: #52A6B3;
  --lit-cyea-500: #348199;
  --lit-cyea-600: #1F6180;
  --lit-cyea-700: #114566;
  --lit-cyea-800: #092F4D;
  --lit-cyea-900: #041D33;

  --lit-mage-50:  #FFF5F7;
  --lit-mage-100: #FEEAEF;
  --lit-mage-200: #FED5E0;
  --lit-mage-300: #F9A9C0;
  --lit-mage-400: #EF7CA1;
  --lit-mage-500: #E25287;
  --lit-mage-600: #CE2F75;
  --lit-mage-700: #B7166A;
  --lit-mage-800: #800060;
  --lit-mage-900: #470046;

  --lit-bric-50:  #FDF8EA;
  --lit-bric-100: #F9F1DC;
  --lit-bric-200: #EFD9AB;
  --lit-bric-300: #E4BC78;
  --lit-bric-400: #D59441;
  --lit-bric-500: #C26412;
  --lit-bric-600: #A93D00;
  --lit-bric-700: #8B2100;
  --lit-bric-800: #6A0C00;
  --lit-bric-900: #470000;

  --lit-neutral-50:  #F8F9FA;
  --lit-neutral-100: #F1F3F4;
  --lit-neutral-200: #E8EAED;
  --lit-neutral-300: #DADCE0;
  --lit-neutral-400: #BDC1C6;
  --lit-neutral-500: #9AA0A6;
  --lit-neutral-600: #80868B;
  --lit-neutral-700: #5F6368;
  --lit-neutral-800: #3C4043;
  --lit-neutral-900: #202124;

  /* LIT Major Tonal Palettes */
  --lit-majtonal-p-50:  #EEFBF8;
  --lit-majtonal-p-100: #D8F2ED;
  --lit-majtonal-p-200: #C0E7E3;
  --lit-majtonal-p-300: #A1D2D4;
  --lit-majtonal-p-400: #72AEB9;
  --lit-majtonal-p-500: #48879C;
  --lit-majtonal-p-600: #326882;
  --lit-majtonal-p-700: #284E67;
  --lit-majtonal-p-800: #1D3649;
  --lit-majtonal-p-900: #142838;

  --lit-majtonal-s-50:  #FFF5F7;
  --lit-majtonal-s-100: #FAEDF0;
  --lit-majtonal-s-200: #F7DBE4;
  --lit-majtonal-s-300: #EDBDCD;
  --lit-majtonal-s-400: #E091AC;
  --lit-majtonal-s-500: #CC6990;
  --lit-majtonal-s-600: #BE4079;
  --lit-majtonal-s-700: #9D2D69;
  --lit-majtonal-s-800: #651A54;
  --lit-majtonal-s-900: #3B0A3C;

  --lit-majtonal-t-50:  #FCF8EF;
  --lit-majtonal-t-100: #F9F7ED;
  --lit-majtonal-t-200: #EDDEBF;
  --lit-majtonal-t-300: #E0C9A2;
  --lit-majtonal-t-400: #CEA269;
  --lit-majtonal-t-500: #B6763E;
  --lit-majtonal-t-600: #A14C1C;
  --lit-majtonal-t-700: #7E351F;
  --lit-majtonal-t-800: #58211B;
  --lit-majtonal-t-900: #3B0A0B;

  --lit-majtonal-nv-50:  #F0F7F7;
  --lit-majtonal-nv-100: #EBF3F2;
  --lit-majtonal-nv-200: #E3ECED;
  --lit-majtonal-nv-300: #CCD9DD;
  --lit-majtonal-nv-400: #B5C6CA;
  --lit-majtonal-nv-500: #9CAFB4;
  --lit-majtonal-nv-600: #72868F;
  --lit-majtonal-nv-700: #596C75;
  --lit-majtonal-nv-800: #3F5259;
  --lit-majtonal-nv-900: #222C35;

  /* LIT Minor Tonal Palettes */
  --lit-mintonal-p-1: #F5F9FA;
  --lit-mintonal-p-2: #EFF5F7;
  --lit-mintonal-p-3: #E9F1F4;
  --lit-mintonal-p-4: #E7F0F3;
  --lit-mintonal-p-5: #E3EDF1;

  --lit-mintonal-s-1: #F9F2F7;
  --lit-mintonal-s-2: #F5EBF2;
  --lit-mintonal-s-3: #F1E3EE;
  --lit-mintonal-s-4: #F0E0EC;
  --lit-mintonal-s-5: #EDDBE9;

  --lit-mintonal-t-1: #FAF4F3;
  --lit-mintonal-t-2: #F6EDEB;
  --lit-mintonal-t-3: #F2E7E3;
  --lit-mintonal-t-4: #F3E4E1;
  --lit-mintonal-t-5: #EFE0DB;

  /* Google Red, Exclusively for Errors */
  --google-red-50: #FCE8E6;
  --google-red-500: #EA4335;
  --google-red-600: #D93025;
  --google-red-700: #C5221F;

  /* Viz Colors */
  --viz-color-orange-1: #FFD8C3;
  --viz-color-orange-2: #F0BD80;
  --viz-color-orange-3: #FF9230;
  --viz-color-orange-4: #BA4A0D;

  --viz-color-blue-1: #87CDF9;
  --viz-color-blue-2: #61AFF7;
  --viz-color-blue-3: #3C7DBF;
  --viz-color-blue-4: #184889;

  --viz-color-yellow-1: #FAF49F;
  --viz-color-yellow-2: #FFE839;
  --viz-color-yellow-3: #FFC700;
  --viz-color-yellow-4: #848014;

  --viz-color-purple-1: #CDC5FF;
  --viz-color-purple-2: #9B86EF;
  --viz-color-purple-3: #7647EA;
  --viz-color-purple-4: #270085;

  --viz-color-coral-1: #F6AEA9;
  --viz-color-coral-2: #FF777B;
  --viz-color-coral-3: #FC4F61;
  --viz-color-coral-4: #B12D33;

  --viz-color-teal-1: #BDF4E7;
  --viz-color-teal-2: #7DDAD3;
  --viz-color-teal-3: #1F978A;
  --viz-color-teal-4: #006067;

  --viz-color-magenta-1: #EDC4E6;
  --viz-color-magenta-2: #EF96CD;
  --viz-color-magenta-3: #B22A72;
  --viz-color-magenta-4: #632440;

  --viz-color-grey-1: #DADCE0;
  --viz-color-grey-2: #B5BCC3;
  --viz-color-grey-3: #879695;
  --viz-color-grey-4: #515050;

  /* Compatibility Aliases */
  --lit-gray-700: var(--lit-neutral-700);
  --lit-gray-800: var(--lit-neutral-700);
  /* For field names, etc. like preds (MulticlassPreds) */
  --lit-bold-label-color: var(--lit-majtonal-nv-800);
  --lit-light-label-color: var(--lit-majtonal-nv-600);

  --lit-box-shadow: 0 2px 2px 0 rgba(0, 0, 0, .14),
                    0 3px 1px -2px rgba(0, 0, 0, .2),
                    0 1px 5px 0 rgba(0, 0, 0, .12);

  /* Semantic (theme-dependent) tokens */
  --lit-background: #F5F9FA;
  --lit-surface: #FFFFFF;
  --lit-surface-variant: #F8F9FA;
  --lit-header-surface: #F5FCFC;
  --lit-hover-bg: #F1F3F4;
  --lit-hover-accent-bg: #E4F7FB;
  --lit-selected-bg: #CDF2FA;
  --lit-selected-fg: #3C4043;
  --lit-primary-selected-bg: #7BCCCC;
  --lit-primary-selected-fg: #000000;
  --lit-row-highlight-bg: #FED5E0;
  --lit-overlay: rgba(4, 29, 51, .47);
  --lit-on-surface: #202124;
  --lit-on-surface-variant: #5F6368;
  --lit-outline: #DADCE0;
  --lit-accent: #098591;
  --lit-accent-bright: #129EAF;
  --lit-accent-deep: #1F6180;
  --lit-button-bg: #FFFFFF;
  --lit-button-border: #A9A9A9;
  --lit-button-hover-bg: #FAF49F;
  --lit-button-disabled-bg: #A9A9A9;
  --lit-button-disabled-fg: #D3D3D3;
  --lit-tooltip-bg: #202124;
  --lit-tooltip-fg: #FFFFFF;
  --lit-tooltip-link: #7BCCCC;
  --lit-chart-tooltip-bg: rgba(255, 255, 255, 0.5);
  --lit-chip-fg: #5F6368;
  --lit-chip-bg: #F8F9FA;
  --lit-chip-hover-bg: #E8EAED;
  --lit-chip-border-selected: #80868B;
  --lit-chip-label-fg: #3C4043;
  --lit-chip-generated-fg: #8430CE;
  --lit-chip-generated-bg: #F3E8FD;
  --lit-chip-generated-hover-bg: #E9D2FD;
  --lit-chip-generated-selected-border: #A142F4;
  --lit-diff-color: #A93D00;
  --lit-edited-bg: #FDF8EA;
  --lit-image-toggle-bg: rgba(211, 211, 211, 0.5);
  --lit-dropdown-arrow: ${DROPDOWN_ARROW_SVG('%233C4043')};
  --lit-dropdown-arrow-active: ${DROPDOWN_ARROW_SVG('%231F6180')};
  --lit-dropdown-arrow-disabled: ${DROPDOWN_ARROW_SVG('%23E8EAED')};

  /* Default (light) color scheme for native controls (scrollbars, inputs) */
  color-scheme: light;

  /* Base text color: inherited into shadow DOM; SVG currentColor too */
  color: var(--lit-on-surface);
}

body {
  background-color: var(--lit-background);
}

html.${DARK_THEME_CLASS} {
  /* Invert the neutral ramp: low values become dark surfaces, high values
   * become light text. */
  --lit-neutral-50:  #202124;
  --lit-neutral-100: #3C4043;
  --lit-neutral-200: #5F6368;
  --lit-neutral-300: #80868B;
  --lit-neutral-400: #9AA0A6;
  --lit-neutral-500: #BDC1C6;
  --lit-neutral-600: #DADCE0;
  --lit-neutral-700: #E8EAED;
  --lit-neutral-800: #F1F3F4;
  --lit-neutral-900: #F8F9FA;

  /* Rotate the neutral-variant ramp so high values stay high-contrast. */
  --lit-majtonal-nv-50:  #222C35;
  --lit-majtonal-nv-100: #3F5259;
  --lit-majtonal-nv-200: #596C75;
  --lit-majtonal-nv-300: #72868F;
  --lit-majtonal-nv-400: #9CAFB4;
  --lit-majtonal-nv-500: #8FA5AB;
  --lit-majtonal-nv-600: #9CAFB4;
  --lit-majtonal-nv-700: #B5C6CA;
  --lit-majtonal-nv-800: #CCD9DD;
  --lit-majtonal-nv-900: #E3ECED;

  /* Minor tonal hover tints, flipped to dark tints that brighten on use. */
  --lit-mintonal-p-1: #1D272A;
  --lit-mintonal-p-2: #212B2E;
  --lit-mintonal-p-3: #263134;
  --lit-mintonal-p-4: #2B3639;
  --lit-mintonal-p-5: #303B3F;

  --lit-mintonal-s-1: #27202A;
  --lit-mintonal-s-2: #2B242E;
  --lit-mintonal-s-3: #302933;
  --lit-mintonal-s-4: #352E38;
  --lit-mintonal-s-5: #3A333D;

  --lit-mintonal-t-1: #2A2524;
  --lit-mintonal-t-2: #2E2928;
  --lit-mintonal-t-3: #332E2D;
  --lit-mintonal-t-4: #383332;
  --lit-mintonal-t-5: #3D3837;

  --lit-box-shadow: 0 2px 2px 0 rgba(0, 0, 0, .4),
                    0 3px 1px -2px rgba(0, 0, 0, .5),
                    0 1px 5px 0 rgba(0, 0, 0, .4);

  /* Semantic (theme-dependent) tokens */
  --lit-background: #17181A;
  --lit-surface: #202124;
  --lit-surface-variant: #292B2E;
  --lit-header-surface: #26292C;
  --lit-hover-bg: #2A2C2F;
  --lit-hover-accent-bg: #1E3A44;
  --lit-selected-bg: #1E3A44;
  --lit-selected-fg: #D7E9EE;
  --lit-primary-selected-bg: #2E6570;
  --lit-primary-selected-fg: #F8F9FA;
  --lit-row-highlight-bg: #4A2B3B;
  --lit-overlay: rgba(0, 0, 0, .6);
  --lit-on-surface: #E8EAED;
  --lit-on-surface-variant: #BDC1C6;
  --lit-outline: #5F6368;
  --lit-accent: #7BCCCC;
  --lit-accent-bright: #7BCCCC;
  --lit-accent-deep: #7BCCCC;
  --lit-button-bg: #2A2C2F;
  --lit-button-border: #5F6368;
  --lit-button-hover-bg: #33363A;
  --lit-button-disabled-bg: #3C4043;
  --lit-button-disabled-fg: #5F6368;
  --lit-tooltip-bg: #E8EAED;
  --lit-tooltip-fg: #202124;
  --lit-tooltip-link: #1F6180;
  --lit-chart-tooltip-bg: rgba(32, 33, 36, 0.8);
  --lit-chip-fg: #BDC1C6;
  --lit-chip-bg: #292B2E;
  --lit-chip-hover-bg: #3C4043;
  --lit-chip-border-selected: #9AA0A6;
  --lit-chip-label-fg: #E8EAED;
  --lit-chip-generated-fg: #D6BBFB;
  --lit-chip-generated-bg: #322545;
  --lit-chip-generated-hover-bg: #3D2E55;
  --lit-chip-generated-selected-border: #C58AF9;
  --lit-diff-color: #E4BC78;
  --lit-edited-bg: #3A3017;
  --lit-image-toggle-bg: rgba(32, 33, 36, 0.6);
  --lit-dropdown-arrow: ${DROPDOWN_ARROW_SVG('%23DADCE0')};
  --lit-dropdown-arrow-active: ${DROPDOWN_ARROW_SVG('%237BCCCC')};
  --lit-dropdown-arrow-disabled: ${DROPDOWN_ARROW_SVG('%235F6368')};

  /* Native controls (scrollbars, form controls, select popups) */
  color-scheme: dark;

  /* Material Web Components theming */
  --mdc-theme-surface: #202124;
  --mdc-theme-background: #202124;
  --mdc-theme-on-surface: #E8EAED;
  --mdc-theme-text-primary-on-background: rgba(232, 234, 237, 0.87);
  --mdc-theme-text-secondary-on-background: rgba(232, 234, 237, 0.6);
  --mdc-theme-text-hint-on-background: rgba(232, 234, 237, 0.5);
  --mdc-theme-text-icon-on-background: rgba(232, 234, 237, 0.5);
  --mdc-checkbox-unchecked-color: rgba(232, 234, 237, 0.7);
  --mdc-checkbox-disabled-color: rgba(232, 234, 237, 0.3);
  --mdc-radio-unchecked-color: rgba(232, 234, 237, 0.7);
  --mdc-radio-disabled-color: rgba(232, 234, 237, 0.3);
  --mdc-text-field-fill-color: #2A2C2F;
  --mdc-text-field-disabled-fill-color: #25272A;
  --mdc-text-field-ink-color: #E8EAED;
  --mdc-text-field-disabled-ink-color: rgba(232, 234, 237, 0.5);
  --mdc-text-field-label-ink-color: rgba(232, 234, 237, 0.6);
  --mdc-text-field-idle-line-color: rgba(232, 234, 237, 0.5);
  --mdc-text-field-hover-line-color: rgba(232, 234, 237, 0.8);
  --mdc-switch-unselected-track-color: rgba(232, 234, 237, 0.3);
  --mdc-switch-unselected-hover-track-color: rgba(232, 234, 237, 0.4);
  --mdc-switch-unselected-focus-track-color: rgba(232, 234, 237, 0.4);
  --mdc-switch-unselected-pressed-track-color: rgba(232, 234, 237, 0.4);
  --mdc-switch-unselected-handle-color: #9AA0A6;
  --mdc-switch-unselected-hover-handle-color: #BDC1C6;
  --mdc-switch-unselected-focus-handle-color: #BDC1C6;
  --mdc-switch-unselected-pressed-handle-color: #BDC1C6;
  --mdc-switch-unselected-icon-color: #202124;
  --mdc-switch-unselected-focus-state-layer-color: rgba(232, 234, 237, 0.1);
  --mdc-switch-unselected-hover-state-layer-color: rgba(232, 234, 237, 0.1);
  --mdc-switch-unselected-pressed-state-layer-color: rgba(232, 234, 237, 0.1);
  --mdc-ripple-color: rgba(232, 234, 237, 0.1);
}
`;

/**
 * Injects the global theme stylesheet into the document head. Idempotent;
 * safe to call from multiple entry points.
 */
export function injectGlobalThemeStyles() {
  if (typeof document === 'undefined') return;
  if (document.getElementById(THEME_STYLE_ELEMENT_ID) != null) return;
  const styleEl = document.createElement('style');
  styleEl.id = THEME_STYLE_ELEMENT_ID;
  styleEl.textContent = GLOBAL_THEME_CSS;
  document.head.prepend(styleEl);
}

/** Returns the user's explicitly stored theme, or null if unset. */
export function getStoredTheme(): Theme|null {
  try {
    const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
    if (stored === 'light' || stored === 'dark') return stored;
  } catch {
    // localStorage may be unavailable (private mode etc.)
  }
  return null;
}

/** Returns the theme matching the OS-level prefers-color-scheme setting. */
export function getSystemTheme(): Theme {
  if (typeof window !== 'undefined' && window.matchMedia != null &&
      window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark';
  }
  return 'light';
}

/** Returns the theme the app should start with. */
export function getInitialTheme(): Theme {
  return getStoredTheme() ?? getSystemTheme();
}

/**
 * Applies the given theme by toggling the `lit-dark` class on `html`.
 * Persists the choice to localStorage when `persist` is true.
 */
export function applyTheme(theme: Theme, persist = false) {
  if (typeof document === 'undefined') return;
  document.documentElement.classList.toggle(
      DARK_THEME_CLASS, theme === 'dark');
  if (persist) {
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch {
      // Ignore storage failures.
    }
  }
}

/**
 * Starts watching the OS-level color scheme. The callback is only invoked
 * when the user has not explicitly chosen a theme.
 */
export function watchSystemTheme(onChange: (theme: Theme) => void) {
  if (typeof window === 'undefined' || window.matchMedia == null) return;
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  const listener = (e: MediaQueryListEvent) => {
    if (getStoredTheme() != null) return;
    onChange(e.matches ? 'dark' : 'light');
  };
  if (mediaQuery.addEventListener != null) {
    mediaQuery.addEventListener('change', listener);
  }
}

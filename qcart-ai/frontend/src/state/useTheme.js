import { useState, useEffect, useCallback } from "react";
import { THEMES, detectTimeTheme, detectContextTheme, applyTheme } from "../lib/theme.js";

export function useTheme() {
  const [themeName, setThemeName] = useState(() => detectTimeTheme());

  useEffect(() => {
    applyTheme(themeName);
  }, [themeName]);

  const setThemeByContext = useCallback((text) => {
    const detected = detectContextTheme(text);
    if (detected) setThemeName(detected);
  }, []);

  const setThemeByName = useCallback((name) => {
    if (THEMES[name]) setThemeName(name);
  }, []);

  const currentTheme = THEMES[themeName] || THEMES.afternoon;

  return {
    currentTheme,
    themeName,
    setThemeByContext,
    setThemeByName,
    isNightMode: currentTheme.isNight,
  };
}

// src/theme.ts
import { createContext, useState, useMemo } from 'react';
import { createTheme } from '@mui/material/styles';

// 1) Tokens de color
export const tokens = (mode: 'light' | 'dark') => ({
  ...(mode === 'dark'
    ? {
        grey: {
          100: "#FFFFFF", // blanco
          200: "#E5E5E5",
          300: "#CCCCCC",
          400: "#B2B2B2",
          500: "#999999",
          600: "#7F7F7F",
          700: "#0c2c4d",
          800: "#141b2d",
          900: "#000000"  // negro
        },
        primary: {
          100: "#d0d1d5",
          200: "#a1a4ab",
          300: "#727681",
          400: "#1F2A40",
          500: "#141b2d",
          600: "#101624",
          700: "#0c101b",
          800: "#080b12",
          900: "#040509",
        },
        greenAccent: {
          100: "#dbf5ee",
          200: "#b7ebde",
          300: "#94e2cd",
          400: "#70d8bd",
          500: "#4cceac",
          600: "rgba(0, 100, 0, 0.6)",
          700: "rgba(0, 0, 0, 0.0)",
          800: "#0c2c4d",
          900: "#000000",
        },
        redAccent: {
          100: "#f8dcdb",
          200: "#f1b9b7",
          300: "#e99592",
          400: "#e2726e",
          500: "#db4f4a",
          600: "#af3f3b",
          700: "#832f2c",
          800: "#58201e",
          900: "#2c100f",
        },
        blueAccent: {
          100: '#e1f0ff',
          200: '#5e8ebf',
          300: '#477db5',
          400: '#306dac',
          500: '#195da3',  // tu centro
          600: '#165493',
          700: '#144a82',
          800: '#124172',
          900: '#0f3862',
        },
        orangeAccent: {
          100: "#ffe0cc",
          200: "#ffc199",
          300: "#ffa166",
          400: "#ff8233",
          500: "#ff6300",
          600: "#bf4a00",
          700: "#803200",
          800: "#401900",
          900: "#000000",
        },
      }
    : {
        grey: {
          100: "#FFFFFF", // blanco
          200: "#E5E5E5",
          300: "#CCCCCC",
          400: "#B2B2B2",
          500: "#999999",
          600: "#7F7F7F",
          700: "#666666",
          800: "#0000ff",
          900: "#000000"  // negro
        },
        primary: {
          100: "#040509",
          200: "#080b12",
          300: "#0c101b",
          400: "#f2f0f0", // manually changed
          500: "#141b2d",
          600: "#1F2A40",
          700: "#727681",
          800: "#a1a4ab",
          900: "#d0d1d5",
        },
        greenAccent: {
          100: "#0f2922",
          200: "#1e5245",
          300: "#2e7c67",
          400: "#3da58a",
          500: "#4cceac",
          600: "rgba(0, 100, 0, 0.6)",
          700: "rgba(0, 0, 0, 0.0)",
          800: "#b7ebde",
          900: "#dbf5ee",
        },
        redAccent: {
          100: "#2c100f",
          200: "#58201e",
          300: "#832f2c",
          400: "#af3f3b",
          500: "#db4f4a",
          600: "#e2726e",
          700: "#e99592",
          800: "#f1b9b7",
          900: "#f8dcdb",
        },
        blueAccent: {
          100: '#e1f0ff',
          200: '#5e8ebf',
          300: '#477db5',
          400: '#306dac',
          500: '#195da3',  // tu centro
          600: '#165493',
          700: '#144a82',
          800: '#124172',
          900: '#0f3862',
        },
        orangeAccent: {
          100: "#ffe0cc",
          200: "#ffc199",
          300: "#ffa166",
          400: "#ff8233",
          500: "#ff6300",
          600: "#bf4a00",
          700: "#803200",
          800: "#401900",
          900: "#000000",
        },
      }),
});

// 2) Settings para createTheme
export const themeSettings = (mode: 'light' | 'dark') => {
  const colors = tokens(mode);
  return {
    palette: {
      mode,
      ...(mode === 'dark'
        ? {
            primary: { main: colors.primary[500] },
            secondary: { main: colors.greenAccent[500] },
            background: { default: colors.primary[500] },
            appbar_azul: { main: colors.grey[700] },
            sidebar: {
                main: colors.grey[900],
                icon: '#88c33c',
                texto: colors.blueAccent[100],
            },
            footer: {
                main: colors.grey[800],
                //icon: colors.orangeAccent[500],
                //texto: colors.blueAccent[500],
            },
            nuevo_btn: {
                main: '#88c33c',
                texto: colors.grey[100],
            },
            editar_btn: {
                main: '#1976d2',
                hover: '#115293',
                texto: '#fff'
            },
            borrar_btn: {
                main: '#d32f2f',
                hover: '#9a0007',
                texto: '#fff'
            },
            guardar_btn: {
              main: '#388e3c',
              hover: '#2e7d32',
              texto: '#fff'
            },
            cancelar_btn: {
              main: '#d32f2f',
              hover: '#9a0007',
              texto: '#fff'
            },
            grid_top: {
              main: colors.blueAccent[900],
            },
            grid_bottom: {
              main: colors.blueAccent[900],
            },
            activo: {
              on:  '#4caf50',  // verde MUI 500
              off: '#d32f2f',  // rojo MUI 700
              form:'#ffab00',  // ámbar MUI A400
            },
            row: {
              dark: 'rgba(255, 255, 255, 0.06)' // ligero blanco en modo oscuro
            },
            qr_btn: {
              main:  '#009688',  // Teal 500
              hover: '#00796b',  // Teal 700
              texto: '#ffffff'
            },
            grafica_btn: {
              main:  '#3f51b5',  // Indigo 500
              hover: '#303f9f',  // Indigo 700
              texto: '#ffffff'
            },
            delta_p: {
              success:  '#5ed551',  
              warning: '#f7ba00', 
              error: '#ff3c4e'
            },
          }
        : {
            primary: { main: colors.primary[100] },
            secondary: { main: colors.greenAccent[500] },
            //background: { default: '#fcfcfc' },
            background: { default: colors.grey[100], },
            appbar_azul: { main: colors.blueAccent[500] },
            sidebar: {
                main: colors.grey[100],
                icon: '#88c33c',
                texto: colors.blueAccent[500],
            },
            footer: {
                main: colors.grey[100],
                //icon: colors.orangeAccent[500],
                //texto: colors.blueAccent[500],
            },
            nuevo_btn: {
                main: '#88c33c',
                //icon: colors.orangeAccent[500],
                texto: colors.grey[100],
            },
            editar_btn: {
              main: '#1976d2',
              hover: '#115293',
              texto: '#fff'
            },
            borrar_btn: {
              main: '#d32f2f',
              hover: '#9a0007',
              texto: '#fff'
            },
            guardar_btn: {
              main: '#388e3c',
              hover: '#2e7d32',
              texto: '#fff'
            },
            cancelar_btn: {
              main: '#d32f2f',
              hover: '#9a0007',
              texto: '#fff'
            },
            grid_top: {
              main: colors.blueAccent[100],
            },
            grid_bottom: {
              main: colors.blueAccent[100],
            },
            activo: {
              on:  '#4caf50',  // verde MUI 500
              off: '#d32f2f',  // rojo MUI 700
              form:'#ffab00',  // ámbar MUI A400
            },
            row: {
              dark: 'rgba(0, 0, 0, 0.04)'
            },
            qr_btn: {
              main:  '#009688',  // Teal 500
              hover: '#00796b',  // Teal 700
              texto: '#ffffff'
            },
            grafica_btn: {
              main:  '#3f51b5',  // Indigo 500
              hover: '#303f9f',  // Indigo 700
              texto: '#ffffff'
            },
            delta_p: {
              success:  '#5ed551',  
              warning: '#f7ba00',  // Indigo 700
              error: '#ff3c4e'
            },
          })
    },
    typography: {
      fontFamily: ['Source Sans Pro','sans-serif'].join(','),
      fontSize: 12,
      h1: { fontSize: 40 },
      h2: { fontSize: 32 },
      /* … resto de tamaños … */
    }
  };
};

// 3) Contexto para toggle
export const ColorModeContext = createContext({ toggleColorMode: () => {} });

// 4) Hook que expone [theme, colorMode]
export const useMode = (): [ReturnType<typeof createTheme>, { toggleColorMode: () => void }] => {
  const [mode, setMode] = useState<'light'|'dark'>('light');
  const colorMode = useMemo(() => ({
    toggleColorMode: () => setMode(prev => prev === 'light' ? 'dark' : 'light')
  }), []);
  const theme = useMemo(() => createTheme(themeSettings(mode)), [mode]);
  return [theme, colorMode];
};

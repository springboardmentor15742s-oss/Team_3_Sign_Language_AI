// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// react-router-dom v7's internals reference TextEncoder/TextDecoder (used
// by the browser Fetch/URL machinery it pulls in), which CRA 5's jsdom
// test environment (an older jsdom bundled with Jest 27) doesn't provide
// as a global the way a real browser or Node's own global scope does.
// Polyfilled from Node's built-in 'util' module — not a mock, the same
// real implementation Node uses elsewhere — so every test that imports
// anything routing-related doesn't crash before it even runs.
import { TextEncoder, TextDecoder } from 'util';

if (typeof (globalThis as any).TextEncoder === 'undefined') {
  (globalThis as any).TextEncoder = TextEncoder;
}
if (typeof (globalThis as any).TextDecoder === 'undefined') {
  (globalThis as any).TextDecoder = TextDecoder;
}

// jsdom doesn't implement window.matchMedia at all (it's not part of the
// DOM spec jsdom targets) — AnimatedNumber.tsx calls it to respect
// prefers-reduced-motion, and any component that renders it would
// otherwise throw "window.matchMedia is not a function" in every test.
// Standard boilerplate polyfill: reports "no match" (not reduced motion),
// which is also the correct default for a headless test environment.
if (typeof window !== 'undefined' && !window.matchMedia) {
  window.matchMedia = (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }) as unknown as MediaQueryList;
}

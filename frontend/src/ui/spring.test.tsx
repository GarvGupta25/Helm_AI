import { expect, it } from 'vitest';
import { project, rubberband, springStep } from './spring';

it('critical spring approaches target without overshoot and settles', () => {
  let state = { value: 200, velocity: 0 };
  for (let i = 0; i < 120; i++) { state = springStep(state, 0, 1 / 60); expect(state.value).toBeGreaterThanOrEqual(0); }
  expect(state.value).toBeCloseTo(0, 4);
});
it('retargeting preserves the current value and momentum instead of restarting', () => {
  const state = springStep({ value: 0, velocity: 0 }, 500, .05, .8, .3);
  const reversed = springStep(state, 0, .001, .8, .3);
  expect(Math.abs(reversed.value - state.value)).toBeLessThan(5);
  expect(reversed.velocity).toBeGreaterThan(0);
});
it('flick release carries velocity and produces a bounded overshoot', () => {
  let state = { value: 80, velocity: -800 }; let minimum = 0;
  for (let i = 0; i < 120; i++) { state = springStep(state, 0, 1 / 120, .8, .3); minimum = Math.min(minimum, state.value); }
  expect(minimum).toBeLessThan(0); expect(minimum).toBeGreaterThan(-20);
  expect(state.value).toBeCloseTo(0, 3);
});
it('rubberband resists progressively and projection keeps velocity direction', () => {
  expect(rubberband(100, 600)).toBeGreaterThan(0); expect(rubberband(100, 600)).toBeLessThan(55);
  expect(rubberband(-100, 600)).toBe(-rubberband(100, 600));
  expect(project(1000)).toBeCloseTo(499); expect(project(-1000)).toBeCloseTo(-499);
});

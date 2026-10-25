export type SpringState = { value: number; velocity: number };

// Closed-form damped spring: retargets preserve both presentation and velocity.
export function springStep(state: SpringState, target: number, seconds: number, damping = 1, response = .35): SpringState {
  const w = 2 * Math.PI / response; const x = state.value - target; const v = state.velocity;
  if (damping >= 1) {
    const b = v + w * x; const decay = Math.exp(-w * seconds);
    return { value: target + (x + b * seconds) * decay, velocity: (v - w * b * seconds) * decay };
  }
  const wd = w * Math.sqrt(1 - damping * damping); const a = damping * w;
  const b = (v + a * x) / wd; const decay = Math.exp(-a * seconds);
  const c = Math.cos(wd * seconds); const s = Math.sin(wd * seconds);
  return { value: target + decay * (x * c + b * s), velocity: decay * ((-a * x + b * wd) * c + (-a * b - x * wd) * s) };
}
export const rubberband = (overshoot: number, dimension: number) => overshoot * dimension * .55 / (dimension + .55 * Math.abs(overshoot));
export const project = (velocity: number) => velocity / 1000 * .998 / (1 - .998);

export function spring(initial: number, render: (value: number) => void, rest?: () => void, precision = .2) {
  let state: SpringState = { value: initial, velocity: 0 }; let target = initial;
  let frame = 0; let previous = 0; let damping = 1; let response = .35;
  function pause() { cancelAnimationFrame(frame); frame = 0; previous = 0; }
  render(initial);
  function tick(time: number) {
    const dt = previous ? Math.min((time - previous) / 1000, .064) : 1 / 60; previous = time;
    state = springStep(state, target, dt, damping, response); render(state.value);
    if (Math.abs(state.value - target) < precision && Math.abs(state.velocity) < precision * 5) {
      state = { value: target, velocity: 0 }; render(target); frame = 0; previous = 0; rest?.();
    } else frame = requestAnimationFrame(tick);
  }
  return {
    get value() { return state.value; }, get velocity() { return state.velocity; },
    pause,
    jump(value: number, velocity = 0) { pause(); state = { value, velocity }; render(value); },
    to(value: number, options: { velocity?: number; damping?: number; response?: number } = {}) {
      target = value; damping = options.damping ?? 1; response = options.response ?? .35;
      if (options.velocity !== undefined) state.velocity = options.velocity;
      if (!frame) frame = requestAnimationFrame(tick);
    },
  };
}

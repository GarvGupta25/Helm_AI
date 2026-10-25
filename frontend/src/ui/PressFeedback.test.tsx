import React from 'react';
import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { PressFeedback } from './PressFeedback';

afterEach(cleanup);
it('starts feedback on down without committing, and clears on cancel', () => {
  const click = vi.fn(); render(<><PressFeedback/><button onClick={click}>Action</button></>);
  const button = screen.getByRole('button');
  const event = new Event('pointerdown', { bubbles: true });
  Object.assign(event, { button: 0, isPrimary: true, pointerId: 1 });
  fireEvent(button, event);
  expect(button.hasAttribute('data-pressed')).toBe(true); expect(click).not.toHaveBeenCalled();
  fireEvent.pointerCancel(document); expect(button.hasAttribute('data-pressed')).toBe(false);
});
it('excludes disabled controls and restores keyboard feedback', () => {
  render(<><PressFeedback/><button disabled>Disabled</button><a href="/">Link</a></>);
  fireEvent.keyDown(screen.getByRole('button'), { key: 'Enter' });
  expect(screen.getByRole('button').hasAttribute('data-pressed')).toBe(false);
  fireEvent.keyDown(screen.getByRole('link'), { key: 'Enter' });
  expect(screen.getByRole('link').hasAttribute('data-pressed')).toBe(true);
  fireEvent.keyUp(document, { key: 'Enter' });
  expect(screen.getByRole('link').hasAttribute('data-pressed')).toBe(false);
});

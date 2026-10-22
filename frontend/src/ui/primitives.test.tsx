import React from 'react';
import { describe, it, expect, vi, afterEach } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Field, Modal, NarrativeTabs, Button, Check } from './primitives';

afterEach(cleanup);
describe('accessible UK controls', () => {
  it('associates labels and error descriptions', () => {
    render(<Field name="postcode" label="Your postcode" error="Enter a valid postcode"/>);
    const field = screen.getByLabelText('Your postcode', { exact: false });
    expect(field.getAttribute('aria-invalid')).toBe('true');
    expect(field.getAttribute('aria-describedby')).toBe('postcode-error');
    expect(screen.getByRole('alert').textContent).toBe('Enter a valid postcode');
  });
  it('exposes modal title and a working close action', () => {
    const close = vi.fn(); render(<Modal title="Review your choices" open onClose={close}><p>Read before continuing.</p></Modal>);
    expect(screen.getByRole('dialog').getAttribute('aria-labelledby')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Close dialog' })); expect(close).toHaveBeenCalled();
  });
  it('makes consent unchecked until the user acts', () => {
    render(<Check>I agree to optional analytics</Check>);
    const check = screen.getByRole('checkbox') as HTMLInputElement;
    expect(check.checked).toBe(false); fireEvent.click(check); expect(check.checked).toBe(true);
  });
  it('keeps disabled actions unavailable', () => {
    const click = vi.fn(); render(<Button disabled onClick={click}>Confirm payment</Button>);
    fireEvent.click(screen.getByRole('button')); expect(click).not.toHaveBeenCalled();
  });
  it('labels narrative tabs and exposes the active panel', () => {
    render(<BrowserRouter><NarrativeTabs/></BrowserRouter>);
    expect(screen.getByRole('tablist', { name: 'Our approach' })).toBeTruthy();
    expect(screen.getByRole('tab', { name: 'Why we exist' }).getAttribute('aria-selected')).toBe('true');
    expect(screen.getByRole('tabpanel').textContent).toContain('decoder ring');
  });
});

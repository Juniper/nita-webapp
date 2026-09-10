import { useEffect, useRef } from 'react'

/**
 * Calls `callback` every `intervalMs` for as long as `active` is true.
 *
 * While `active` is false no timer exists and no calls are made, so a screen
 * with nothing in progress costs nothing. The timer is cleared when `active`
 * becomes false and on unmount.
 *
 * The latest `callback` is held in a ref so that a caller passing an unstable
 * function does not restart the interval on every render.
 */
export function usePollWhile(
  active: boolean,
  callback: () => void,
  intervalMs: number,
): void {
  const savedCallback = useRef(callback)

  useEffect(() => {
    savedCallback.current = callback
  }, [callback])

  useEffect(() => {
    if (!active) return
    const timer = setInterval(() => savedCallback.current(), intervalMs)
    return () => clearInterval(timer)
  }, [active, intervalMs])
}

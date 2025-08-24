import React, { useEffect, useState } from 'react';
import { SSE as SSEjs, SSEvent } from 'sse.js';
import { Props as BaseProps } from '../components/SSE'; // reuse the interface

declare global {
  interface Window {
    dash_clientside?: {
      set_props?: (componentId: string, props: any) => void;
    };
  }
}

interface Props extends BaseProps {
  update_component?: any;
}

const SSE = ({
  url,
  options,
  concat = true,
  setProps,
  done,
  update_component,
}: Props) => {
  const [data, setData] = useState<string>('');
  const [doneData, setDoneData] = useState<boolean>(done || false);

  useEffect(() => {
    // Reset on URL change.
    setDoneData(false);
    setData('');
    if (!url) {
      return;
    }
    // Instantiate EventSource.
    const sse = new SSEjs(url, options);
    sse.onmessage = (e: SSEvent) => {
      // Handle end of stream.
      if (e.data === '[DONE]') {
        setDoneData(true);
        sse.close();
        return;
      }
      // Update value.
      // setData((prev) => (concat ? prev.concat(e.data) : e.data));
      // If update_component is set, try to parse and update Dash component
      const dashSetProps = window.dash_clientside?.set_props;
      if (update_component && dashSetProps) {
        try {
          // Expecting SSE message to be a JSON array: [_, componentId, props] or [componentId, props]
          const msg = JSON.parse(e.data);
          if (Array.isArray(msg)) {
            // If 3 elements, ignore the first (status); if 2, use both
            const componentId = msg.length === 3 ? msg[1] : msg[0];
            const props = msg.length === 3 ? msg[2] : msg[1];
            dashSetProps(componentId, props);
          }
        } catch (err) {
          // Not a JSON message, ignore
          console.log("Not a JSON message, ignoring for update_component", e.data)
        }
      }
    };
    sse.onerror = (e: Event) => {
      console.log('ERROR', e);
      sse.close();
    };
    // Close on unmount.
    return () => {
      sse.close();
    };
  }, [url, options, concat]);

  useEffect(() => {
    if (setProps) {
      setProps({
        value: data,
        done: doneData,
      });
    }
  }, [data, doneData, setProps]);

  return <></>;
};

export default SSE;

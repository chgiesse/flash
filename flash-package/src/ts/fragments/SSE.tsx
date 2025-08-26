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
      // If update_component is set, try to parse and update Dash component
      const dashSetProps = window.dash_clientside?.set_props;
      if (update_component && dashSetProps) {
        try {
          const msg = JSON.parse(e.data);
          if (Array.isArray(msg)) {
            const [stream_type, componentId, props] = msg

            switch (stream_type) {
              case '[ERROR]':
                if (props.handle_error) {
                  window.alert(`Error from SSE stream: ${props.error}`);
                }

                if (props.reset_props) {
                  props.reset_props.forEach((item: any) => {
                    if (Array.isArray(item) && item.length === 2) {
                      const [compId, compProps] = item;
                      dashSetProps(compId, compProps);
                    }
                  });
                }
                sse.close()
                break;

              case '[SINGLE]':
                dashSetProps(componentId, props);
                break;

              case '[BATCH]':
                // For batch, we expect props to be a list of list of [componentId, props]
                if (Array.isArray(props)) {
                  props.forEach((item: any) => {
                    if (Array.isArray(item) && item.length === 2) {
                      const [compId, compProps] = item;
                      dashSetProps(compId, compProps);
                    }
                  });
                }
                break;

              default:
                console.warn('Unknown stream type:', stream_type);
            }
          }
        } catch (err) {
          // Not a JSON message, ignore
          console.log("Not a JSON message, ignoring for update_component", e.data)
        }
      }
    };
    sse.onerror = (e: Event) => {
      console.log('Unhandled SSE ERROR', e);
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

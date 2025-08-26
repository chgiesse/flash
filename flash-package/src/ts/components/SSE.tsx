import React, { Suspense } from 'react';
import { SSEOptions } from 'sse.js';
import { DashComponentProps } from '../props';

const LazySSE = React.lazy(() => import(/* webpackChunkName: "SSE" */ '../fragments/SSE'));

export type Props = DashComponentProps & {
  /**
   * Options passed to the SSE constructor.
   */
  options?: SSEOptions;
  /**
   * URL of the endpoint.
   */
  url?: string;
  /**
   * A boolean indicating if the stream values should be concatenated.
   */
  concat?: boolean;
  /**
   * The data value. Either the latest, or the concatenated depending on the `concat` property.
   */
  value?: string;
  /**
   * A boolean indicating if the (current) stream has ended.
   */
  done?: boolean;
  /**
   * A boolean indicating if the strea, should update components.
   */
  update_component?: boolean;
};

/**
 * The SSE component makes it possible to collect data from e.g. a ResponseStream. It's a wrapper around the SSE.js library.
 * https://github.com/mpetazzoni/sse.js
 */
const SSE = (props: Props) => {
  return (
    <Suspense fallback={<></>}>
      <LazySSE {...props} />
    </Suspense>
  );
};

export default SSE;

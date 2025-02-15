import { Box } from '@mui/material';
import { useEffect, useRef } from 'react';

let tvScriptLoadingPromise: Promise<void>;

const TradingViewWidget = () => {
  const onLoadScriptRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    onLoadScriptRef.current = createWidget;

    if (!tvScriptLoadingPromise) {
      tvScriptLoadingPromise = new Promise(resolve => {
        const script = document.createElement('script');
        script.id = 'tradingview-widget-loading-script';
        script.src = 'https://s3.tradingview.com/tv.js';
        script.type = 'text/javascript';
        script.onload = resolve as () => void;

        document.head.appendChild(script);
      });
    }

    tvScriptLoadingPromise.then(() => onLoadScriptRef.current?.());

    return () => {
      onLoadScriptRef.current = null;
    };
  }, []);

  const createWidget = () => {
    if (document.getElementById('tradingview-widget') && 'TradingView' in window) {
      const tv = (window as any).TradingView;
      new tv.widget({
        autosize: true,
        symbol: 'BINANCE:ETHUSDT',
        interval: '1',
        timezone: 'exchange',
        theme: 'dark',
        style: '1',
        locale: 'en',
        toolbar_bg: '#f1f3f6',
        enable_publishing: false,
        allow_symbol_change: true,
        container_id: 'tradingview-widget',
      });
    }
  };

  return (
    <Box
      id="tradingview-widget"
      sx={{
        height: '100%',
        width: '100%',
      }}
    />
  );
};

export default TradingViewWidget;

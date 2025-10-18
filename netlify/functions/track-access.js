// Netlify Function: アクセストラッキング
// NHKからのアクセスを検出してログに記録

exports.handler = async (event, context) => {
  const clientIP = event.headers['x-nf-client-connection-ip'] ||
                   event.headers['client-ip'];
  const userAgent = event.headers['user-agent'];
  const referer = event.headers['referer'] || 'Direct';
  const timestamp = new Date().toISOString();
  const path = event.queryStringParameters.path || 'unknown';

  // NHKのIPレンジをチェック（例）
  const isNHK = checkNHKIP(clientIP);

  const logEntry = {
    timestamp,
    ip: clientIP,
    userAgent,
    referer,
    path,
    isNHK,
    country: event.headers['x-country'] || 'unknown'
  };

  // ログ出力（Netlify Logsで確認可能）
  console.log('ACCESS_LOG:', JSON.stringify(logEntry));

  // NHKからのアクセスの場合は特別にマーク
  if (isNHK) {
    console.log('🚨 NHK ACCESS DETECTED:', JSON.stringify(logEntry));
  }

  return {
    statusCode: 200,
    body: JSON.stringify({ tracked: true })
  };
};

// NHKのIPレンジをチェック（IPv4/IPv6対応）
function checkNHKIP(ip) {
  if (!ip) return false;

  // NHKの既知のIPv4レンジ
  const nhkIPv4Ranges = [
    '210.171.',  // NHK放送センター等
    '202.218.',  // NHK関連
    '133.205.',  // 一部のNHK施設
  ];

  // NHKの既知のIPv6レンジ（わかる範囲で追加）
  const nhkIPv6Ranges = [
    '2001:200:900:',  // NHK関連IPv6（推定）
  ];

  // IPv4チェック
  if (nhkIPv4Ranges.some(range => ip.startsWith(range))) {
    return true;
  }

  // IPv6チェック
  if (nhkIPv6Ranges.some(range => ip.toLowerCase().startsWith(range.toLowerCase()))) {
    return true;
  }

  return false;
}

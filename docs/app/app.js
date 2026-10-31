/* mailforen Web Analyzer — fully client-side OSINT helpers + UI. No build step, no deps. */
'use strict';

// ---------------------------------------------------------------- reference data
var POPULAR_DOMAINS = ['gmail.com','outlook.com','yahoo.com','hotmail.com','icloud.com','proton.me','protonmail.com','aol.com','live.com','msn.com','mail.com','zoho.com','gmx.com','yandex.com','mail.ru'];
var DISPOSABLE_DOMAINS = ['mailinator.com','guerrillamail.com','10minutemail.com','tempmail.com','throwawaymail.com','yopmail.com','getnada.com','trashmail.com','sharklasers.com','dispostable.com','maildrop.cc','fakeinbox.com','tempinbox.com','spam4.me','grr.la','mytemp.email','mailnesia.com','temp-mail.org','mohmal.com','emailondeck.com','burnermail.io','mailcatch.com','mintemail.com','tempmailaddress.com','throwam.com','1secmail.com','inboxbear.com'];
var IMPERSONATION_TARGETS = ['paypal.com','apple.com','icloud-support.com','amazon.com','netflix.com','microsoft.com','facebook.com','instagram.com','whatsapp.com','coinbase.com','binance.com','dhl.com','fedex.com','usps.com','irs.gov','hmrc.gov.uk'];
var URL_SHORTENERS = ['bit.ly','t.co','tinyurl.com','goo.gl','is.gd','cutt.ly','rb.gy','ow.ly','buff.ly','rebrand.ly','s.id','shorturl.at','tiny.cc','bit.do','lnkd.in'];
var SUSPICIOUS_TLDS = ['zip','mov','top','xyz','tk','ml','ga','cf','gq','click','loan','quest','rest','review','country','download','stream','icu','buzz','monster'];

// ---------------------------------------------------------------- pure helpers
function editDistance(a, b) {
  var m = a.length, n = b.length;
  var dp = [];
  for (var i = 0; i <= m; i++) dp.push([i].concat(new Array(n).fill(0)));
  for (var j = 0; j <= n; j++) dp[0][j] = j;
  for (var i2 = 1; i2 <= m; i2++)
    for (var j2 = 1; j2 <= n; j2++)
      dp[i2][j2] = Math.min(dp[i2-1][j2] + 1, dp[i2][j2-1] + 1, dp[i2-1][j2-1] + (a[i2-1] !== b[j2-1] ? 1 : 0));
  return dp[m][n];
}

function detectTarget(s) {
  s = String(s || '').trim();
  if (/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(s)) return 'email';
  if (/^https?:\/\//i.test(s)) return 'url';
  if (/^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$/i.test(s)) return 'domain';
  return 'unknown';
}

function emailSyntaxOk(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email);
}

function detectTypoSquat(domain) {
  var d = String(domain || '').toLowerCase();
  var best = null;
  var targets = IMPERSONATION_TARGETS.concat(POPULAR_DOMAINS);
  for (var i = 0; i < targets.length; i++) {
    var p = targets[i];
    if (d === p) return null;
    var dist = editDistance(d, p);
    if (dist <= 2 && (!best || dist < best.distance)) best = { closest: p, distance: dist };
  }
  return best;
}

function isDisposable(domain) { return DISPOSABLE_DOMAINS.indexOf(String(domain).toLowerCase()) !== -1; }
function isFreeProvider(domain) { return POPULAR_DOMAINS.indexOf(String(domain).toLowerCase()) !== -1; }

function unfoldHeaders(raw) {
  return String(raw || '').replace(/\r\n/g, '\n').replace(/\n([ \t]+)/g, ' ');
}

function parseHeaders(unfoldedBlock) {
  var out = [];
  var lines = String(unfoldedBlock || '').split('\n');
  for (var i = 0; i < lines.length; i++) {
    var line = lines[i];
    if (!line.trim()) break;
    var m = /^([\w-]+):\s*(.*)$/.exec(line);
    if (m) out.push({ name: m[1], value: m[2] });
  }
  return out;
}

function splitEml(raw) {
  var text = String(raw || '').replace(/\r\n/g, '\n');
  var idx = text.indexOf('\n\n');
  var head = idx === -1 ? text : text.slice(0, idx);
  var body = idx === -1 ? '' : text.slice(idx + 2);
  return { headerBlock: unfoldHeaders(head), body: body };
}

function parseReceivedChain(headerBlock) {
  var headers = parseHeaders(unfoldHeaders(headerBlock));
  var rec = headers.filter(function (h) { return h.name.toLowerCase() === 'received'; }).map(function (h) { return h.value; });
  return rec.map(function (v, i) {
    var from = /\bfrom\s+([^\s;()]+)/i.exec(v);
    var by = /\bby\s+([^\s;()]+)/i.exec(v);
    var withM = /\bwith\s+([^\s;()]+)/i.exec(v);
    var date = /;\s*(.+)$/.exec(v);
    return {
      hop: rec.length - i,
      from: from ? from[1] : null,
      by: by ? by[1] : null,
      with: withM ? withM[1] : null,
      date: date ? date[1].trim() : null,
      raw: v
    };
  });
}

function parseAuthResults(headerBlock) {
  var out = [];
  var headers = parseHeaders(unfoldHeaders(headerBlock));
  var rx = /\b(spf|dkim|dmarc)\s*=\s*(pass|fail|softfail|neutral|none|temperror|permerror)/gi;
  for (var i = 0; i < headers.length; i++) {
    if (headers[i].name.toLowerCase() !== 'authentication-results') continue;
    var res = { spf: null, dkim: null, dmarc: null, raw: headers[i].value };
    var m;
    rx.lastIndex = 0;
    while ((m = rx.exec(headers[i].value))) res[m[1].toLowerCase()] = m[2].toLowerCase();
    out.push(res);
  }
  return out;
}

function parseSpf(txt) {
  if (!txt || !/v=spf1/i.test(txt)) return null;
  var terms = String(txt).trim().split(/\s+/).slice(1);
  var all = null;
  for (var i = 0; i < terms.length; i++) {
    var m = /^([+\-~?])?all$/i.exec(terms[i]);
    if (m) all = m[1] || '+';
  }
  return { text: String(txt).trim(), terms: terms, allQualifier: all, openAll: all === '+' };
}

function parseDmarc(txt) {
  if (!txt || !/v\s*=\s*dmarc1/i.test(txt)) return null;
  var tags = {};
  var re = /([a-zA-Z]+)\s*=\s*([^;]+)/g, m;
  while ((m = re.exec(txt))) tags[m[1].toLowerCase()] = m[2].trim();
  return { tags: tags, policy: tags.p || null };
}

function extractUrls(text) {
  var out = [];
  var re = /https?:\/\/[^\s<>"')\]]+/gi, m;
  while ((m = re.exec(String(text || '')))) {
    var u = m[0].replace(/[.,;:]+$/, '');
    if (out.indexOf(u) === -1) out.push(u);
  }
  return out;
}

function parseEmailAddr(v) {
  if (!v) return null;
  var m = /<([^>]+)>/.exec(v);
  var addr = (m ? m[1] : v).trim();
  var at = addr.lastIndexOf('@');
  if (at === -1) return { addr: addr, local: addr, domain: null };
  return { addr: addr, local: addr.slice(0, at), domain: addr.slice(at + 1).toLowerCase() };
}

function parseEml(raw, nowMs) {
  var parts = splitEml(raw);
  var headers = parseHeaders(parts.headerBlock);
  function get(name) {
    for (var i = 0; i < headers.length; i++) if (headers[i].name.toLowerCase() === name) return headers[i].value;
    return null;
  }
  var from = parseEmailAddr(get('from'));
  var replyTo = parseEmailAddr(get('reply-to'));
  var returnPath = parseEmailAddr(get('return-path'));
  var msgId = get('message-id');
  var dateRaw = get('date');
  var dateParsed = dateRaw ? new Date(dateRaw) : null;
  var urls = extractUrls(raw);
  return {
    headers: headers,
    subject: get('subject'),
    from: from,
    replyTo: replyTo,
    returnPath: returnPath,
    messageId: msgId,
    messageIdDomain: msgId ? (parseEmailAddr(msgId.replace(/^<|>$/g, '')) || {}).domain : null,
    dateRaw: dateRaw,
    dateParsed: dateParsed,
    dateAgeDays: dateParsed && !isNaN(dateParsed.getTime())
      ? Math.round(((nowMs || Date.now()) - dateParsed.getTime()) / 86400000)
      : null,
    urls: urls,
    mismatchFromReplyTo: !!(from && replyTo && from.domain && replyTo.domain && from.domain !== replyTo.domain),
    mismatchFromReturnPath: !!(from && returnPath && from.domain && returnPath.domain && from.domain !== returnPath.domain),
    mismatchFromMessageId: !!(from && from.domain && msgId && msgId.indexOf('@') !== -1 &&
      msgId.slice(msgId.indexOf('@')).toLowerCase().indexOf(from.domain) === -1)
  };
}

function analyzeUrlHeuristics(url) {
  var checks = [];
  var u;
  try { u = new URL(url); } catch (e) { return [{ title: 'URL parse', status: 'fail', detail: 'Could not parse URL' }]; }
  var host = u.hostname.toLowerCase();

  checks.push({
    title: 'Scheme',
    status: u.protocol === 'https:' ? 'pass' : 'fail',
    detail: u.protocol + ' — ' + (u.protocol === 'https:' ? 'TLS transport' : 'plaintext HTTP, no transport security')
  });
  checks.push({
    title: 'IP literal host',
    status: /^\d{1,3}(\.\d{1,3}){3}$/.test(host) || host.indexOf(':') !== -1 ? 'fail' : 'pass',
    detail: 'host=' + host + (/^\d{1,3}(\.\d{1,3}){3}$/.test(host) ? ' — raw IP address, hides domain reputation' : '')
  });
  checks.push({
    title: 'Punycode / homoglyph',
    status: host.indexOf('xn--') !== -1 ? 'fail' : 'pass',
    detail: host.indexOf('xn--') !== -1 ? 'host contains punycode labels (possible IDN homoglyph attack)' : 'no punycode labels'
  });
  checks.push({
    title: 'Credentials in URL',
    status: u.username || u.password ? 'fail' : 'pass',
    detail: u.username || u.password ? 'userinfo embedded — classic phishing obfuscation' : 'no userinfo'
  });
  var port = u.port ? parseInt(u.port, 10) : (u.protocol === 'https:' ? 443 : 80);
  checks.push({
    title: 'Port',
    status: (port === 80 || port === 443) ? 'pass' : 'warn',
    detail: 'port ' + port
  });
  var labels = host.split('.');
  checks.push({
    title: 'Subdomain depth',
    status: labels.length > 4 ? 'warn' : 'pass',
    detail: labels.length + ' labels: ' + host
  });
  checks.push({
    title: 'URL shortener',
    status: URL_SHORTENERS.indexOf(host) !== -1 ? 'warn' : 'pass',
    detail: URL_SHORTENERS.indexOf(host) !== -1 ? host + ' hides the true destination' : 'not a known shortener'
  });
  var tld = labels[labels.length - 1];
  checks.push({
    title: 'TLD reputation',
    status: SUSPICIOUS_TLDS.indexOf(tld) !== -1 ? 'fail' : 'info',
    detail: 'TLD .' + tld + (SUSPICIOUS_TLDS.indexOf(tld) !== -1 ? ' — heavily abused TLD' : '')
  });
  checks.push({
    title: 'URL length',
    status: url.length > 120 ? 'warn' : 'pass',
    detail: url.length + ' chars'
  });
  return checks;
}

// ---------------------------------------------------------------- network (browser only)
function fetchJSON(url, opts, timeoutMs) {
  opts = opts || {};
  var ctrl = typeof AbortController !== 'undefined' ? new AbortController() : null;
  var t = ctrl ? setTimeout(function () { ctrl.abort(); }, timeoutMs || 8000) : null;
  var init = ctrl ? Object.assign({}, opts, { signal: ctrl.signal }) : opts;
  return fetch(url, init).then(function (r) {
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  }).finally(function () { if (t) clearTimeout(t); });
}

function dohQuery(name, type) {
  return fetchJSON('https://dns.google/resolve?name=' + encodeURIComponent(name) + '&type=' + type)
    .catch(function () {
      return fetchJSON('https://cloudflare-dns.com/dns-query?name=' + encodeURIComponent(name) + '&type=' + type,
        { headers: { accept: 'application/dns-json' } });
    });
}

function ctLookup(domain) {
  return fetchJSON('https://crt.sh/?q=' + encodeURIComponent(domain) + '&output=json', {}, 12000);
}

// ---------------------------------------------------------------- analysis (browser orchestration)
function answerRecords(resp, wantType) {
  if (!resp || resp.Status !== 0 || !resp.Answer) return [];
  return resp.Answer.filter(function (a) { return !wantType || a.type === wantType; });
}

function domainCards(name) {
  var cards = [];
  function card(title, status, detail, evidence) { cards.push({ title: title, status: status, detail: detail, evidence: evidence || [] }); }

  return dohQuery(name, 'MX').then(function (mx) {
    var recs = answerRecords(mx, '15');
    if (recs.length) {
      var hosts = recs.map(function (r) { return r.data; });
      card('MX records', 'pass', recs.length + ' mail exchanger(s) — domain can receive mail', hosts);
      card('Mail provider hint', 'info', hosts.join(' ').toLowerCase().indexOf('google') !== -1 ? 'Google Workspace'
        : hosts.join(' ').toLowerCase().indexOf('outlook') !== -1 || hosts.join(' ').toLowerCase().indexOf('protection.outlook') !== -1 ? 'Microsoft 365'
        : 'custom mail setup');
    } else {
      card('MX records', 'warn', 'No MX records — this domain cannot receive email');
    }
    return dohQuery(name, 'A');
  }).then(function (a) {
    var recs = answerRecords(a, '1');
    card('A record', recs.length ? 'info' : 'warn', recs.length ? recs.map(function (r) { return r.data; }).join(', ') : 'no A record');
    return dohQuery(name, 'TXT');
  }).then(function (txt) {
    var recs = answerRecords(txt, '16').map(function (r) { return String(r.data).replace(/^"|"$/g, ''); });
    var spfRec = null;
    for (var i = 0; i < recs.length; i++) if (/^v=spf1/i.test(recs[i])) spfRec = recs[i];
    if (spfRec) {
      var spf = parseSpf(spfRec);
      card('SPF', spf.openAll ? 'fail' : spf.allQualifier === '~' ? 'warn' : 'pass',
        spf.openAll ? 'SPF ends in +all — any host may send mail for this domain (spoofable)'
          : 'all-qualifier "' + spf.allQualifier + '"' , [spfRec]);
    } else {
      card('SPF', 'warn', 'No SPF record found on apex', recs.slice(0, 5));
    }
    return dohQuery('_dmarc.' + name, 'TXT');
  }).then(function (d) {
    var recs = answerRecords(d, '16').map(function (r) { return String(r.data).replace(/^"|"$/g, ''); });
    var dmarcRec = null;
    for (var i = 0; i < recs.length; i++) if (/v\s*=\s*dmarc1/i.test(recs[i])) dmarcRec = recs[i];
    if (dmarcRec) {
      var dm = parseDmarc(dmarcRec);
      card('DMARC', dm.policy === 'quarantine' || dm.policy === 'reject' ? 'pass' : 'warn',
        'policy p=' + (dm.policy || 'missing') + (dm.policy === 'none' ? ' — monitoring only, spoofing not blocked' : ''), [dmarcRec]);
    } else {
      card('DMARC', 'warn', 'No DMARC record — receiving servers decide how to treat spoofed mail');
    }
    return dohQuery(name, 'DNSKEY');
  }).then(function (k) {
    var recs = answerRecords(k, '48');
    card('DNSSEC', recs.length ? 'pass' : 'info', recs.length ? 'DNSKEY published — domain is DNSSEC-signed' : 'no DNSKEY (common; unsigned zone)');
    return ctLookup(name).catch(function () { return null; });
  }).then(function (ct) {
    if (ct === null) {
      card('Certificate Transparency (crt.sh)', 'info', 'CT lookup unavailable (crt.sh unreachable or timed out)');
    } else {
      var seen = {}, uniq = [];
      for (var i = 0; i < ct.length && uniq.length < 5; i++) {
        var nv = String(ct[i].name_value || '').replace(/\n/g, ' ');
        if (!seen[nv]) { seen[nv] = 1; uniq.push(nv); }
      }
      card('Certificate Transparency', ct.length > 0 ? 'info' : 'warn',
        ct.length + ' certificate(s) logged for ' + name, uniq);
    }
    return cards;
  }).catch(function (e) {
    cards.push({ title: 'DNS lookup error', status: 'fail', detail: String(e && e.message || e) });
    return cards;
  });
}

function emailCards(target) {
  var cards = [];
  var parsed = parseEmailAddr(target);
  if (!emailSyntaxOk(target)) {
    cards.push({ title: 'Email syntax', status: 'fail', detail: 'Does not look like a valid email address' });
    return Promise.resolve(cards);
  }
  cards.push({ title: 'Email syntax', status: 'pass', detail: 'Valid RFC-style address: ' + parsed.addr });
  if (isDisposable(parsed.domain)) cards.push({ title: 'Disposable domain', status: 'fail', detail: parsed.domain + ' is a known disposable/temp-mail provider' });
  else cards.push({ title: 'Disposable domain', status: 'pass', detail: parsed.domain + ' is not on the disposable list' });
  if (isFreeProvider(parsed.domain)) cards.push({ title: 'Provider type', status: 'info', detail: 'Free public mail provider: ' + parsed.domain });
  var typo = detectTypoSquat(parsed.domain);
  if (typo) cards.push({ title: 'Typo-squatting', status: 'fail', detail: 'Domain is ' + typo.distance + ' edit(s) from "' + typo.closest + '" — likely impersonation' });
  return domainCards(parsed.domain).then(function (dc) { return cards.concat(dc); });
}

function urlCards(target) {
  var cards = analyzeUrlHeuristics(target);
  var host;
  try { host = new URL(target).hostname; } catch (e) { return Promise.resolve(cards); }
  return domainCards(host).then(function (dc) { return cards.concat(dc); });
}

function emlCards(raw) {
  var eml = parseEml(raw, Date.now());
  var cards = [];
  function card(title, status, detail, evidence) { cards.push({ title: title, status: status, detail: detail, evidence: evidence || [] }); }

  var hops = parseReceivedChain(eml.headers.map(function (h) { return h.name + ': ' + h.value; }).join('\n'));
  if (hops.length) {
    card('Received chain', 'info', hops.length + ' hop(s), hop 1 = originating machine. Read bottom-up for the true path.',
      hops.map(function (h) { return '#' + h.hop + ' from ' + (h.from || '?') + ' by ' + (h.by || '?') + (h.with ? ' with ' + h.with : '') + (h.date ? ' @ ' + h.date : ''); }));
  } else {
    card('Received chain', 'warn', 'No Received headers found');
  }

  var auths = parseAuthResults(eml.headers.map(function (h) { return h.name + ': ' + h.value; }).join('\n'));
  if (auths.length) {
    var a = auths[0];
    var spfSt = a.spf === 'pass' ? 'pass' : (a.spf === 'softfail' || a.spf === 'neutral' || a.spf === 'none') ? 'warn' : 'fail';
    var dmarcSt = a.dmarc === 'pass' ? 'pass' : 'fail';
    var dkimSt = a.dkim === 'pass' ? 'pass' : (a.dkim === 'none' ? 'info' : 'fail');
    card('SPF (sender policy)', spfSt, 'Authentication-Results: spf=' + (a.spf || 'absent'), [a.raw]);
    card('DKIM (signature)', dkimSt, 'Authentication-Results: dkim=' + (a.dkim || 'absent'), [a.raw]);
    card('DMARC (alignment)', dmarcSt, 'Authentication-Results: dmarc=' + (a.dmarc || 'absent'), [a.raw]);
  } else {
    card('Authentication-Results', 'warn', 'No Authentication-Results header — verification not attested');
  }

  if (eml.from) card('From address', 'info', eml.from.addr + ' (domain: ' + eml.from.domain + ')');
  if (eml.mismatchFromReplyTo) card('Reply-To mismatch', 'fail', 'Reply-To (' + eml.replyTo.domain + ') differs from From (' + eml.from.domain + ') — replies go to the attacker');
  if (eml.mismatchFromReturnPath) card('Return-Path mismatch', 'warn', 'Return-Path (' + eml.returnPath.domain + ') differs from From (' + eml.from.domain + ') — possible spoofing or mailing-list forward');
  if (eml.mismatchFromMessageId) card('Message-ID domain mismatch', 'warn', 'Message-ID domain does not match From domain (' + eml.from.domain + ')');
  if (eml.dateAgeDays !== null) {
    card('Date check', (eml.dateAgeDays > 90 || eml.dateAgeDays < -1) ? 'warn' : 'pass',
      'Date: ' + eml.dateRaw + ' (age: ' + eml.dateAgeDays + ' day(s))');
  }

  if (eml.urls.length) {
    var urlEvidence = eml.urls.slice(0, 10).map(function (u) {
      var bad = analyzeUrlHeuristics(u).filter(function (c) { return c.status === 'fail'; }).map(function (c) { return c.title; });
      return u + (bad.length ? '  [' + bad.join(', ') + ']' : '');
    });
    card('Extracted URLs', eml.urls.length > 5 ? 'warn' : 'info', eml.urls.length + ' URL(s) in the message', urlEvidence);
  } else {
    card('Extracted URLs', 'info', 'No http(s) URLs found');
  }

  var fromDomain = eml.from && eml.from.domain;
  return (fromDomain ? domainCards(fromDomain) : Promise.resolve([])).then(function (dc) { return cards.concat(dc); });
}

// ---------------------------------------------------------------- browser UI
if (typeof window !== 'undefined' && typeof document !== 'undefined') {
  var state = {
    currentType: 'email',
    currentTarget: '',
    currentCards: [],
    elements: {}
  };

  function esc(s) { return String(s).replace(/&/g, "&").replace(/</g, "<").replace(/>/g, ">"); }

  function badgeClass(status) { return 'result-badge ' + status; }
  function badgeLabel(status) { return ({ pass: 'PASS', warn: 'WARN', fail: 'FAIL', info: 'INFO' })[status] || status.toUpperCase(); }

  function renderCards(cards) {
    var grid = state.elements.resultsGrid;
    var empty = state.elements.resultsEmpty;
    var exportBtn = state.elements.exportBtn;

    if (!cards || !cards.length) {
      grid.innerHTML = '';
      empty.style.display = 'flex';
      exportBtn.disabled = true;
      return;
    }

    empty.style.display = 'none';
    exportBtn.disabled = false;
    state.currentCards = cards;

    var html = '';
    for (var i = 0; i < cards.length; i++) {
      var c = cards[i];
      var ev = '';
      if (c.evidence && c.evidence.length) {
        ev = '<ul class="result-evidence">' + c.evidence.map(function (e) { return '<li>' + esc(e) + '</li>'; }).join('') + '</ul>';
      }
      html += '<div class="result-card" style="animation-delay: ' + (i * 40) + 'ms">'
        + '<div class="result-card-head">'
        + '<span class="' + badgeClass(c.status) + '">' + badgeLabel(c.status) + '</span>'
        + '<h3 class="result-title">' + esc(c.title) + '</h3>'
        + '</div>'
        + '<p class="result-detail">' + esc(c.detail) + '</p>'
        + ev
        + '</div>';
    }
    grid.innerHTML = html;
  }

  function setLoading(message) {
    var grid = state.elements.resultsGrid;
    var empty = state.elements.resultsEmpty;
    empty.style.display = 'none';
    grid.innerHTML = '<div class="result-card" style="animation-delay: 0ms">'
      + '<div class="result-card-head">'
      + '<span class="result-badge info">LOADING</span>'
      + '<h3 class="result-title">Analyzing…</h3>'
      + '</div>'
      + '<p class="result-detail">' + esc(message) + '</p>'
      + '</div>';
  }

  function runAnalysis(type, target) {
    state.currentType = type;
    state.currentTarget = target;
    var p;
    if (type === 'email') p = emailCards(target);
    else if (type === 'url') p = urlCards(target);
    else if (type === 'domain') p = domainCards(target);
    else { renderCards([{ title: 'Input', status: 'fail', detail: 'Could not classify input' }]); return; }
    p.then(renderCards).catch(function (e) {
      renderCards([{ title: 'Error', status: 'fail', detail: String(e && e.message || e) }]);
    });
  }

  function runRaw(text) {
    state.currentType = 'raw';
    state.currentTarget = text.slice(0, 100);
    setLoading('Parsing raw message…');
    emlCards(text).then(renderCards).catch(function (e) {
      renderCards([{ title: 'Error', status: 'fail', detail: String(e && e.message || e) }]);
    });
  }

  function clearResults() {
    state.currentCards = [];
    state.currentTarget = '';
    var grid = state.elements.resultsGrid;
    var empty = state.elements.resultsEmpty;
    var exportBtn = state.elements.exportBtn;
    grid.innerHTML = '';
    empty.style.display = 'flex';
    exportBtn.disabled = true;
    // Clear inputs
    state.elements.searchEmail.value = '';
    state.elements.searchDomain.value = '';
    state.elements.searchUrl.value = '';
    state.elements.searchRaw.value = '';
  }

  function exportResults() {
    if (!state.currentCards.length) return;
    var data = {
      target: state.currentTarget,
      type: state.currentType,
      timestamp: new Date().toISOString(),
      results: state.currentCards
    };
    var blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'mailforen-analysis-' + Date.now() + '.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function switchTab(type) {
    state.currentType = type;
    // Update tabs
    document.querySelectorAll('.search-tab').forEach(function (tab) {
      var isActive = tab.dataset.type === type;
      tab.classList.toggle('active', isActive);
      tab.setAttribute('aria-selected', isActive);
    });
    // Update panels
    document.querySelectorAll('.search-panel').forEach(function (panel) {
      var isActive = panel.id === 'panel-' + type;
      panel.classList.toggle('active', isActive);
    });
  }

  function initTerminalDemo() {
    var terminal = document.getElementById('terminal-demo');
    if (!terminal) return;
    var lines = terminal.querySelectorAll('.terminal-line');
    var delay = 0;
    lines.forEach(function (line, i) {
      line.style.opacity = '0';
      line.style.transform = 'translateY(10px)';
      line.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
      setTimeout(function () {
        line.style.opacity = '1';
        line.style.transform = 'translateY(0)';
      }, delay);
      delay += 300;
    });
    // Loop animation
    setTimeout(function loop() {
      lines.forEach(function (line) {
        line.style.opacity = '0';
        line.style.transform = 'translateY(-10px)';
      });
      setTimeout(function () {
        lines.forEach(function (line, i) {
          setTimeout(function () {
            line.style.opacity = '1';
            line.style.transform = 'translateY(0)';
          }, i * 300);
        });
      }, 800);
      setTimeout(loop, 8000);
    }, 8000);
  }

  function initHeroCanvas() {
    var canvas = document.querySelector('.hero-canvas');
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    var particles = [];
    var width, height;
    var animationId;

    function resize() {
      var rect = canvas.parentElement.getBoundingClientRect();
      width = canvas.width = rect.width;
      height = canvas.height = rect.height;
    }

    function createParticle() {
      return {
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        radius: Math.random() * 1.5 + 0.5,
        opacity: Math.random() * 0.5 + 0.1,
        color: Math.random() > 0.5 ? '124, 58, 237' : '6, 182, 212'
      };
    }

    function init() {
      resize();
      particles = [];
      for (var i = 0; i < 60; i++) particles.push(createParticle());
    }

    function animate() {
      ctx.clearRect(0, 0, width, height);
      for (var i = 0; i < particles.length; i++) {
        var p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = 0;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(' + p.color + ', ' + p.opacity + ')';
        ctx.fill();
      }
      // Draw connections
      for (var i = 0; i < particles.length; i++) {
        for (var j = i + 1; j < particles.length; j++) {
          var dx = particles[i].x - particles[j].x;
          var dy = particles[i].y - particles[j].y;
          var dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 120) {
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = 'rgba(124, 58, 237, ' + (0.05 * (1 - dist / 120)) + ')';
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      }
      animationId = requestAnimationFrame(animate);
    }

    window.addEventListener('resize', function () {
      init();
    });

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      return;
    }

    init();
    animate();
  }

  document.addEventListener('DOMContentLoaded', function () {
    // Cache elements
    state.elements = {
      searchEmail: document.getElementById('search-email'),
      searchDomain: document.getElementById('search-domain'),
      searchUrl: document.getElementById('search-url'),
      searchRaw: document.getElementById('search-raw'),
      rawFile: document.getElementById('raw-file'),
      resultsGrid: document.getElementById('results'),
      resultsEmpty: document.querySelector('.results-empty'),
      exportBtn: document.getElementById('btn-export'),
      clearBtn: document.getElementById('btn-clear')
    };

    // Tab switching
    document.querySelectorAll('.search-tab').forEach(function (tab) {
      tab.addEventListener('click', function () {
        switchTab(this.dataset.type);
      });
    });

    // Analyze buttons
    document.getElementById('btn-analyze-email').addEventListener('click', function () {
      var val = state.elements.searchEmail.value.trim();
      if (val) runAnalysis('email', val);
    });
    document.getElementById('btn-analyze-domain').addEventListener('click', function () {
      var val = state.elements.searchDomain.value.trim();
      if (val) runAnalysis('domain', val);
    });
    document.getElementById('btn-analyze-url').addEventListener('click', function () {
      var val = state.elements.searchUrl.value.trim();
      if (val) runAnalysis('url', val);
    });
    document.getElementById('btn-analyze-raw').addEventListener('click', function () {
      var val = state.elements.searchRaw.value.trim();
      if (val) runRaw(val);
    });

    // Enter key handlers
    [state.elements.searchEmail, state.elements.searchDomain, state.elements.searchUrl].forEach(function (input) {
      input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
          e.preventDefault();
          var btn = document.getElementById('btn-analyze-' + this.id.replace('search-', ''));
          if (btn) btn.click();
        }
      });
    });

    // File upload
    state.elements.rawFile.addEventListener('change', function (e) {
      var f = e.target.files && e.target.files[0];
      if (!f) return;
      var r = new FileReader();
      r.onload = function () {
        state.elements.searchRaw.value = String(r.result);
        runRaw(String(r.result));
      };
      r.readAsText(f);
      this.value = '';
    });

    // Clear & Export
    state.elements.clearBtn.addEventListener('click', clearResults);
    state.elements.exportBtn.addEventListener('click', exportResults);

    // URL query param support
    var q = new URLSearchParams(location.search).get('target');
    var qType = new URLSearchParams(location.search).get('type') || 'email';
    if (q) {
      switchTab(qType);
      var input = state.elements['search' + qType.charAt(0).toUpperCase() + qType.slice(1)];
      if (input) input.value = q;
      runAnalysis(qType, q);
    }

    // Billing toggle
    var billingToggle = document.getElementById('billing-toggle');
    if (billingToggle) {
      billingToggle.addEventListener('change', function () {
        var isYearly = this.checked;
        document.querySelectorAll('.pricing-amount[data-monthly]').forEach(function (el) {
          el.textContent = isYearly ? el.dataset.yearly : el.dataset.monthly;
        });
        document.querySelectorAll('.pricing-period').forEach(function (el) {
          el.textContent = isYearly ? '/month (billed yearly)' : '/month';
        });
      });
    }

    // Init animations
    initTerminalDemo();
    initHeroCanvas();

    // Expose for debugging
    window.mailforenAnalyze = {
      domainCards: domainCards,
      emailCards: emailCards,
      urlCards: urlCards,
      emlCards: emlCards,
      runAnalysis: runAnalysis,
      runRaw: runRaw
    };
  });
}

// ---------------------------------------------------------------- node export (tests)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    POPULAR_DOMAINS: POPULAR_DOMAINS,
    IMPERSONATION_TARGETS: IMPERSONATION_TARGETS,
    DISPOSABLE_DOMAINS: DISPOSABLE_DOMAINS,
    URL_SHORTENERS: URL_SHORTENERS,
    SUSPICIOUS_TLDS: SUSPICIOUS_TLDS,
    editDistance: editDistance,
    detectTarget: detectTarget,
    emailSyntaxOk: emailSyntaxOk,
    detectTypoSquat: detectTypoSquat,
    isDisposable: isDisposable,
    isFreeProvider: isFreeProvider,
    unfoldHeaders: unfoldHeaders,
    parseHeaders: parseHeaders,
    splitEml: splitEml,
    parseReceivedChain: parseReceivedChain,
    parseAuthResults: parseAuthResults,
    parseSpf: parseSpf,
    parseDmarc: parseDmarc,
    extractUrls: extractUrls,
    parseEmailAddr: parseEmailAddr,
    parseEml: parseEml,
    analyzeUrlHeuristics: analyzeUrlHeuristics
  };
}
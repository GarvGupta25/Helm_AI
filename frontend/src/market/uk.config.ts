export const ukMarket = Object.freeze({
  locale: 'en-GB', currency: 'GBP', timeZone: 'Europe/London',
  iptStandardRate: 0.12, demo: true, phone: '0800 [TBC]',
  firmName: '[FIRM NAME]', frn: '[TBC]', companyNumber: '[TBC]',
  icoNumber: '[TBC]', address: '[ADDRESS TBC]', panelScope: 'Fictional demonstration panel',
  languages: ['en'] as const, verifiedCredentials: [] as string[],
});
export const pounds = (pence: number) => new Intl.NumberFormat(ukMarket.locale, { style: 'currency', currency: ukMarket.currency }).format(pence / 100);

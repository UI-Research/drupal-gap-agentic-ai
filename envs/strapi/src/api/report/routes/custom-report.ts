export default {
  routes: [
    {
      method: 'GET',
      path: '/reports/summary',
      handler: 'report.summary',
      config: {
        auth: false,
        policies: [],
        middlewares: [],
      },
    },
  ],
};

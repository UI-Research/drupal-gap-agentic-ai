export default {
  routes: [
    {
      method: 'GET',
      path: '/reports/summary',
      handler: 'api::report.report.find',
      config: {
        policies: ['global::is-authenticated'],
        middlewares: [],
      },
    },
  ],
};

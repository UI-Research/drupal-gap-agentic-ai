export default {
  routes: [
    {
      method: 'GET',
      path: '/api/settings',
      handler: 'api::settings.settings.get',
      config: {
        policies: [],
      },
    },
    {
      method: 'PUT',
      path: '/api/settings',
      handler: 'api::settings.settings.update',
      config: {
        policies: [],
      },
    },
  ],
};

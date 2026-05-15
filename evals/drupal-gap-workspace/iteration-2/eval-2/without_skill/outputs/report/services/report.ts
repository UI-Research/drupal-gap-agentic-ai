import { factories } from '@strapi/strapi';

export default factories.createCoreService('api::report.report', ({ strapi }) => ({
  async findPublished() {
    return strapi.documents('api::report.report').findMany({
      status: 'published',
    });
  },
}));

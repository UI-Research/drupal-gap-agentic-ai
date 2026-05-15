import { factories } from '@strapi/strapi';

export default factories.createCoreController('api::report.report', ({ strapi }) => ({
  async find(ctx) {
    const documents = await strapi.documents('api::report.report').findMany({
      status: 'published',
    });

    return ctx.send({ data: documents });
  },

  async findOne(ctx) {
    const { id } = ctx.params;
    const document = await strapi.documents('api::report.report').findOne({
      documentId: id,
      status: 'published',
    });

    if (!document) {
      return ctx.notFound('Report not found');
    }

    return ctx.send({ data: document });
  },
}));

import { factories } from '@strapi/strapi';

const coreController = factories.createCoreController('api::report.report');

export default {
  ...coreController,

  async summary(ctx) {
    const documents = await strapi.documents('api::report.report').findMany({
      status: 'published',
      fields: ['title', 'body'],
    });

    const summary = {
      total: documents.length,
      reports: documents.map((doc) => ({
        id: doc.documentId,
        title: doc.title,
      })),
    };

    return ctx.send(summary);
  },
};

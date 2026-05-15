<?php

namespace Drupal\reports\Controller;

use Drupal\reports\Service\ArticleReporter;
use Drupal\Core\Controller\ControllerBase;
use Symfony\Component\DependencyInjection\ContainerInterface;
use Symfony\Component\HttpFoundation\JsonResponse;

/**
 * Controller for the /reports route.
 */
class ReportsController extends ControllerBase {

  /**
   * The article reporter service.
   *
   * @var \Drupal\reports\Service\ArticleReporter
   */
  protected $articleReporter;

  /**
   * Constructs a ReportsController object.
   *
   * @param \Drupal\reports\Service\ArticleReporter $article_reporter
   *   The article reporter service.
   */
  public function __construct(ArticleReporter $article_reporter) {
    $this->articleReporter = $article_reporter;
  }

  /**
   * {@inheritdoc}
   */
  public static function create(ContainerInterface $container): static {
    return new static(
      $container->get('reports.article_reporter'),
    );
  }

  /**
   * Returns published Article nodes as JSON.
   *
   * @return \Symfony\Component\HttpFoundation\JsonResponse
   *   A JSON response containing published articles.
   */
  public function list(): JsonResponse {
    $articles = $this->articleReporter->getPublishedArticles();

    return new JsonResponse([
      'data' => $articles,
    ]);
  }

}

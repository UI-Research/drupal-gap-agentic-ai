<?php

namespace Drupal\reports\Controller;

use Drupal\Core\Controller\ControllerBase;
use Symfony\Component\HttpFoundation\JsonResponse;

/**
 * Controller for the reports endpoint.
 */
class ReportsController extends ControllerBase {

  /**
   * Returns a JSON list of published Article nodes.
   */
  public function list(): JsonResponse {
    $storage = $this->entityTypeManager()->getStorage('node');
    $query = $storage->getQuery()
      ->condition('type', 'article')
      ->condition('status', 1)
      ->accessCheck(TRUE)
      ->sort('created', 'DESC');
    $nids = $query->execute();

    $nodes = $storage->loadMultiple($nids);
    $results = [];

    foreach ($nodes as $node) {
      $results[] = [
        'nid' => (int) $node->id(),
        'title' => $node->getTitle(),
        'created' => (int) $node->getCreatedTime(),
      ];
    }

    return new JsonResponse($results);
  }

}

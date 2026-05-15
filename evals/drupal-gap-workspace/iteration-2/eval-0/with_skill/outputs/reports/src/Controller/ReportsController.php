<?php

namespace Drupal\reports\Controller;

use Drupal\Core\Controller\ControllerBase;
use Symfony\Component\HttpFoundation\JsonResponse;

class ReportsController extends ControllerBase {

  public function list(): JsonResponse {
    $query = \Drupal::entityQuery('node')
      ->condition('type', 'article')
      ->condition('status', 1)
      ->accessCheck(TRUE);
    $nids = $query->execute();

    $nodes = \Drupal::entityTypeManager()
      ->getStorage('node')
      ->loadMultiple($nids);

    $data = [];
    foreach ($nodes as $node) {
      $data[] = [
        'id' => $node->id(),
        'title' => $node->label(),
        'created' => $node->getCreatedTime(),
      ];
    }

    return new JsonResponse($data);
  }

}

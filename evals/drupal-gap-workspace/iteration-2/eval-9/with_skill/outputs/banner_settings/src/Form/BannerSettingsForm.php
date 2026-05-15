<?php

namespace Drupal\banner_settings\Form;

use Drupal\Core\Form\ConfigFormBase;
use Drupal\Core\Form\FormStateInterface;

class BannerSettingsForm extends ConfigFormBase {

  public function getFormId(): string {
    return 'banner_settings_settings_form';
  }

  protected function getEditableConfigNames(): array {
    return ['banner_settings.settings'];
  }

  public function buildForm(array $form, FormStateInterface $form_state): array {
    $config = $this->config('banner_settings.settings');

    $form['banner_message'] = [
      '#type' => 'textfield',
      '#title' => $this->t('Banner message'),
      '#default_value' => $config->get('banner_message'),
      '#description' => $this->t('The message to display in the site banner.'),
    ];

    $form['banner_enabled'] = [
      '#type' => 'checkbox',
      '#title' => $this->t('Enable banner'),
      '#default_value' => $config->get('banner_enabled'),
    ];

    return parent::buildForm($form, $form_state);
  }

  public function submitForm(array &$form, FormStateInterface $form_state): void {
    $this->config('banner_settings.settings')
      ->set('banner_message', $form_state->getValue('banner_message'))
      ->set('banner_enabled', $form_state->getValue('banner_enabled'))
      ->save();

    parent::submitForm($form, $form_state);
  }

}

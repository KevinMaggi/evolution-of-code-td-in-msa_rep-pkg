# Filter real MSA or industrial MSA demo

> Author: Kevin Maggi
> 
> Email: kevin.maggi@stud.unifi.it / kevin.maggi@edu.unifi.it

In this filtering step all the repos have been inspected manually in order to only those that contains real MSA
applications or industrial MSA demo. In this classification are included:

 - real MSA applications;
 - industrial demos that present MSA;
 - starter kits for MSA applications with predefined microservices;
 - template for MSA applications with predefined microservices;
 - big-tech related demos that present MSA (like the ones developed by groups of employees of Microsoft, Alibaba, 
Oracle, etc.).

Instead, the following types of repos are not included in the classification:

- non-MSA applications;
- portions or components of MSA applications (like monitors, gateway, etc. for MSA);
- single microservices;
- toy MSA applications;
- academic MSA demo;
- free-time-developed MSA applications/demo;
- examples, tutorials, samples or guides for MSA from books, blogs, articles, sites or lectures.

The selection has been done by inspecting the GitHub description of the repos and the Readme; in absence of clear clues
about the nature of the repo itself, also additional documentation (like sites) has been inspected; in case of further
doubt, as final ratio, has been inspected the content of the repo (like docker-compose files or the structure of the 
code).

The input file, i.e. the current dataset, is at `../../data/dataset/04_filtered_long_time_docker.csv`.

The output file, i.e. the only MSA dataset, must be at `../../data/dataset/05_filtered_msa_only.csv`.

<hr>

> reference date: 15/09/2023

Actual filtering results:

| REPO                                                                        |   MSA?   | TYPE                           |
|-----------------------------------------------------------------------------|:--------:|--------------------------------|
| https://github.com/1-Platform/one-platform                                  | &#10003; |                                |
| https://github.com/Abdulrhman5/StreetOfThings                               | &#10003; |                                |
| https://github.com/AntonioFalcaoJr/EventualShop                             |          | Non-industry demo              |
| https://github.com/CyanAsterisk/FreeCar                                     | &#10003; |                                |
| https://github.com/CyanAsterisk/TikGok                                      | &#10003; |                                |
| https://github.com/EdwinVW/pitstop                                          | &#10003; |                                |
| https://github.com/Elojah/game_01                                           | &#10003; |                                |
| https://github.com/IBM/application-modernization-javaee-quarkus             |          | Guide                          |
| https://github.com/LeonKou/NetPro                                           |          | Dev tool                       |
| https://github.com/LiskHQ/lisk-service                                      |          | MSA infrastructure component   |
| https://github.com/Lomray-Software/microservices                            | &#10003; |                                |
| https://github.com/MarioCarrion/todo-api-microservice-example               |          | Tutorial                       |
| https://github.com/Mikaelemmmm/go-zero-looklook                             |          | Guide                          |
| https://github.com/NTHU-LSALAB/NTHU-Distributed-System                      |          | Non-industry demo              |
| https://github.com/Netflix/conductor                                        |          | MSA infrastructure component   |
| https://github.com/OMKE/ULA                                                 |          | non MSA                        |
| https://github.com/OpenCodeFoundation/eSchool                               | &#10003; |                                |
| https://github.com/OpenLMIS/openlmis-ref-distro                             |          | Documentation                  |
| https://github.com/QuickCorp/QCObjects                                      |          | Framework                      |
| https://github.com/RobyFerro/go-web                                         |          | Framework                      |
| https://github.com/SabaCell/Nike                                            |          | Framework                      |
| https://github.com/Satont/twir                                              | &#10003; |                                |
| https://github.com/Shyam-Chen/Express-Starter                               |          | Other                          |
| https://github.com/ThoreauZZ/spring-cloud-example                           | &#10003; |                                |
| https://github.com/VasilisGaitanidis/master-containerized-microservices     |          | Non-industry sample            |
| https://github.com/VilledeMontreal/workit                                   |          | Framework                      |
| https://github.com/abixen/abixen-platform                                   | &#10003; |                                |
| https://github.com/ahmsay/Solidvessel                                       |          | Toy MSA                        |
| https://github.com/aliyun/alibabacloud-microservice-demo                    | &#10003; |                                |
| https://github.com/andrechristikan/ack-nestjs-boilerplate-kafka             |          | Single microservice            |
| https://github.com/apache/apisix-website                                    |          | Documentation                  |
| https://github.com/asc-lab/micronaut-microservices-poc                      | &#10003; |                                |
| https://github.com/aura-nw/horoscope                                        | &#10003; |                                |
| https://github.com/authorizerdev/authorizer                                 |          | Single microservice            |
| https://github.com/banzaicloud/pipeline                                     |          | Dev platform                   |
| https://github.com/bartstc/booking-app                                      |          | Non-industry example           |
| https://github.com/bee-travels/bee-travels-node                             | &#10003; |                                |
| https://github.com/benc-uk/smilr                                            | &#10003; |                                |
| https://github.com/benjsicam/nodejs-graphql-microservices                   | &#10003; |                                |
| https://github.com/bitlum/payserver                                         |          | Single microservice            |
| https://github.com/buildlyio/buildly-core                                   |          | MSA infrastructure component   |
| https://github.com/camunda-community-hub/zeebe-client-node-js               |          | Library                        |
| https://github.com/camunda/zeebe                                            |          | MSA infrastructure component   |
| https://github.com/cloudblue/django-cqrs                                    | &#10003; |                                |
| https://github.com/danstarns/idio-graphql                                   |          | Library                        |
| https://github.com/davesag/competing-services-example                       |          | Non-industry example           |
| https://github.com/di-unipi-socc/DockerFinder                               | &#10003; |                                |
| https://github.com/dotnet-architecture/eShopOnContainers                    | &#10003; |                                |
| https://github.com/dustinsgoodman/serverless-microservices-graphql-template |          | Other                          |
| https://github.com/east-eden/server                                         | &#10003; |                                |
| https://github.com/fabric8-services/fabric8-wit                             |          | Other                          |
| https://github.com/flolu/centsideas                                         | &#10003; |                                |
| https://github.com/gbourniq/django-on-aws                                   |          | Non-industry sample            |
| https://github.com/geoserver/geoserver-cloud                                | &#10003; |                                |
| https://github.com/go-eagle/eagle                                           |          | Framework                      |
| https://github.com/go-saas/kit                                              | &#10003; |                                |
| https://github.com/golevelup/nestjs                                         |          | Other                          |
| https://github.com/hekate-io/hekate                                         |          | Library                        |
| https://github.com/infraboard/keyauth                                       |          | Dev tool                       |
| https://github.com/instana/robot-shop                                       | &#10003; |                                |
| https://github.com/ivanpaulovich/clean-architecture-manga                   | &#10003; |                                |
| https://github.com/jrcichra/smartcar                                        | &#10003; |                                |
| https://github.com/juicycleff/ultimate-backend                              | &#10003; |                                |
| https://github.com/jvalue/ods                                               | &#10003; |                                |
| https://github.com/kiwicom/the-zoo                                          |          | Dev tool                       |
| https://github.com/kriswep/graphql-microservices                            |          | Non-industry example           |
| https://github.com/kube-tarian/tarian                                       |          | Other                          |
| https://github.com/kubeshop/tracetest                                       |          | Dev tool                       |
| https://github.com/learningOrchestra/mlToolKits                             | &#10003; |                                |
| https://github.com/letsdoitworld/World-Cleanup-Day                          | &#10003; |                                |
| https://github.com/logzio/apollo                                            |          | Dev tool                       |
| https://github.com/lwinterface/panini                                       |          | Framework                      |
| https://github.com/madflojo/tarmac                                          |          | dev utility                    |
| https://github.com/mailgun/gubernator                                       |          | MSA infrastructure component   |
| https://github.com/mehdihadeli/ecommerce-microservices                      |          | Non-industry sample            |
| https://github.com/meysamhadeli/booking-microservices                       |          | Non-industry demo              |
| https://github.com/micro-company/go-auth                                    |          | Single microservice            |
| https://github.com/microrealestate/microrealestate                          | &#10003; |                                |
| https://github.com/microservices-demo/microservices-demo                    |          | Deployment scripts             |
| https://github.com/microservices-patterns/ftgo-application                  |          | Book example                   |
| https://github.com/microsoft/dotnet-podcasts                                | &#10003; |                                |
| https://github.com/minghsu0107/go-random-chat                               | &#10003; |                                |
| https://github.com/minos-framework/ecommerce-example                        | &#10003; |                                |
| https://github.com/moorara/microservices-demo                               |          | Non-industry demo              |
| https://github.com/moov-io/paygate                                          |          | Single microservice            |
| https://github.com/nashtech-garage/yas                                      | &#10003; |                                |
| https://github.com/nestjs/nest                                              |          | Framework                      |
| https://github.com/netcorebcn/quiz                                          | &#10003; |                                |
| https://github.com/open-telemetry/opentelemetry-demo                        | &#10003; |                                |
| https://github.com/openflagr/flagr                                          |          | Single microservice            |
| https://github.com/oracle-quickstart/oci-cloudnative                        | &#10003; |                                |
| https://github.com/oracle-quickstart/oci-micronaut                          | &#10003; |                                |
| https://github.com/orbitalapi/orbital                                       |          | Other                          |
| https://github.com/otasoft/otasoft-api                                      |          | MSA infrastructure component   |
| https://github.com/pace/bricks                                              |          | Library                        |
| https://github.com/pagarme/superbowleto                                     |          | Single microservice            |
| https://github.com/pagarme/tldr                                             |          | Single microservice            |
| https://github.com/pvarentsov/virus-scanner                                 |          | Single microservice            |
| https://github.com/qlik-oss/mira                                            |          | MSA infrastructure component   |
| https://github.com/rajadilipkolli/spring-boot-microservices-series-v2       | &#10003; |                                |
| https://github.com/remorses/mongoke                                         |          | Other                          |
| https://github.com/rodrigorodrigues/microservices-design-patterns           |          | Exercise in style              |
| https://github.com/santoshshinde2012/node-boilerplate                       |          | Template without microservices |
| https://github.com/shortlink-org/shortlink                                  |          | Edu example                    |
| https://github.com/sitkoru/Sitko.Core                                       |          | Library                        |
| https://github.com/spo-iitk/ras-backend                                     | &#10003; |                                |
| https://github.com/spring-cloud/spring-cloud-consul                         |          | MSA component                  |
| https://github.com/spring-cloud/spring-cloud-vault                          |          | MSA dev component              |
| https://github.com/sqshq/piggymetrics                                       |          | Tutorial                       |
| https://github.com/stefanprodan/syros                                       |          | Dev tool                       |
| https://github.com/teixeira-fernando/EcommerceApp                           |          | Non-industry demo              |
| https://github.com/temporalio/temporal                                      |          | MSA infrastructure component   |
| https://github.com/thanhtinhpas1/ViSpeech                                   |          | Non-industry example           |
| https://github.com/thingsboard/thingsboard                                  | &#10003; |                                |
| https://github.com/totvs/tjf-samples                                        |          | Multiple industry samples      |
| https://github.com/tsukhu/nxplorerjs-microservice-starter                   | &#10003; |                                |
| https://github.com/wayofdev/next-starter-tpl                                | &#10003; |                                |
| https://github.com/wework/grabbit                                           |          | MSA infrastructure component   |
| https://github.com/xmlking/micro-starter-kit                                | &#10003; |                                |
| https://github.com/yarpc/yarpc-go                                           |          | MSA infrastructure component   |
| https://github.com/zalando/nakadi                                           |          | MSA infrastructure component   |

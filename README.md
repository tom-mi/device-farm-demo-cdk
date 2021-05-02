# device-farm-demo-cdk

Demo containing
* lambda backed custom resources to create AWS Device farm projects & device pools implemented with the [Provider Framework](https://docs.aws.amazon.com/cdk/api/latest/docs/custom-resources-readme.html#provider-framework)
* pipeline building & running a Device Farm example project
* infrastructure deployed via CDK

## Deploy pipeline & custom resources

```
pushd infrastructure
yarn
yarn cdk deploy --all
popd
```

## Push sources to trigger pipeline

```
./push_sources.sh
```

